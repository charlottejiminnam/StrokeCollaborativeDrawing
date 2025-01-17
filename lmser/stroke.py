import numpy as np
# import tensorflow as tf
from . import inference
import os

class Line:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        
def calculate_proportion(input, output):
    cumsum_input = np.cumsum(input[0], axis=0)
    cumsum_output = np.cumsum(output[0], axis=0)

    input_x = [point[0] for point in cumsum_input]
    input_y = [point[1] for point in cumsum_input]

    input_x_max = np.max(input_x)
    input_x_min = np.min(input_x)
    input_y_max = np.max(input_y)
    input_y_min = np.min(input_y)

    output_x = [point[0] for point in cumsum_output]
    output_y = [point[1] for point in cumsum_output]

    output_x_max = np.max(output_x)
    output_x_min = np.min(output_x)
    output_y_max = np.max(output_y)
    output_y_min = np.min(output_y)

    input_width = input_x_max - input_x_min
    input_height = input_y_max - input_y_min

    output_width = output_x_max - output_x_min
    output_height = output_y_max - output_y_min

    factor_x = input_width / output_width
    factor_y = input_height / output_height

    return factor_x, factor_y


def calculate_distance(p1, p2):
    w = (p1[0] - p2[0]) * (p1[0] - p2[0])
    h = (p1[1] - p2[1]) * (p1[1] - p2[1])
    return (w + h) ** (0.5)


def xy2line(cumsum):
    lines = []
    for i in range(1, len(cumsum)):
        if cumsum[i - 1][2] == 0:  # 연속된 두 점이 모두 pen_state가 0인 경우
            p1 = (cumsum[i - 1][0], cumsum[i - 1][1])
            p2 = (cumsum[i][0], cumsum[i][1])
            line = Line(p1, p2)
            lines.append(line)
    return lines


def line2xy(lines):
    cumsum = []
    for l in range(len(lines)):
        if l == 0: # 첫 번째 stroke
            if lines[l].p1 == (0, 0):
                cumsum.append([lines[l].p2[0], lines[l].p2[1], 0])
            else:
                cumsum.append([lines[l].p1[0], lines[l].p1[1], 0])
                cumsum.append([lines[l].p2[0], lines[l].p2[1], 0])
        else:
            if lines[l].p1 == lines[l - 1].p2: # 연속된 line
                cumsum.append([lines[l].p2[0], lines[l].p2[1], 0])
            else: # 끊어진 line
                cumsum[len(cumsum) - 1][2] = 1 
                cumsum.append([lines[l].p1[0], lines[l].p1[1], 0])
                cumsum.append([lines[l].p2[0], lines[l].p2[1], 0])
    cumsum[len(cumsum) - 1][2] = 1
    return cumsum


def print_line(lines):
    for i in range(0, len(lines)):
        print("p1: ", lines[i].p1)
        print("p2: ", lines[i].p2)


def find_nearest_point(line, coord):
    distance1 = calculate_distance(line.p1, coord)
    distance2 = calculate_distance(line.p2, coord)
    if distance1 <= distance2:
        return 1
    else:
        return 2
        

def find_nearest_strokes(q, input_data, result_data, stroke_n):
    # result_data = result['test']
    # input_data = input['test']
    # print("shape of input_data, result_data", input_data.shape, result_data.shape)

    input_n = len(input_data[0])  # input stroke의 개수
    result_n = len(result_data[0])  # output stroke의 개수

    selected = result_data[:, input_n:, :]
    
    '''
    # scaling ~
    input_1 = input_data[:, :q, :]
    result_1 = result_data[:, :q, :]

    factor_x, factor_y = calculate_proportion(input_1, result_1)

    selected[:, :, 0] *= factor_x
    selected[:, :, 1] *= factor_y

    selected = np.round(selected).astype(int)
    # ~ scaling
    '''

    # 스케일링 수정 ~
    scale_factor = 44.18034
    selected[:, :2] *= scale_factor
    selected = np.round(selected).astype(int)
    # ~ 스케일링 수정
    
    # [dx, dy, pen_state] -> [x, y, pen_state] ~
    points = selected[0]
    dxdy = points[:, :2]  # (dx, dy) 부분
    pen = points[:, 2:]  # pen_state 부분

    # dxdy[:, 1] = - dxdy[:, 1]
    xy = np.cumsum(dxdy, axis=0)

    cumsum = np.concatenate((xy, pen), axis=-1)

    start_point = np.array([0, 0, 0])
    if result_data[0][len(input_data) - 1][2] == 1:
        start_point = np.array([0, 0, 1])
        
    cumsum = np.vstack((start_point, cumsum))
    # ~ [dx, dy, pen_state] -> [x, y, pen_state]

    # 수정 ~
    lines = xy2line(cumsum)
    
    selected_lines = []
    
    coord = (0, 0)
    if stroke_n > len(lines):
        stroke_n = len(lines)
    for s in range(0, stroke_n): # stroke_n 개의 line을 선택
        min_distance = 10000
        min_index = 0
        for d in range(len(lines)):
            point = find_nearest_point(lines[d], coord)
            distance = 0
            if point == 1:
                distance = calculate_distance(lines[d].p1, coord)
            else:
                distance = calculate_distance(lines[d].p2, coord)
                
            if min_distance > distance:
                min_distance = distance
                min_index = d
                
        point = find_nearest_point(lines[min_index], coord)

        if point == 2:
            temp = lines[min_index].p1
            lines[min_index].p1 = lines[min_index].p2
            lines[min_index].p2 = temp
        coord = lines[min_index].p2
        selected_lines.append(lines[min_index])
        lines.pop(min_index)
        
        s = s + 1
    print("selected line : ",len(selected_lines))
    cumsum = line2xy(selected_lines)
    selected = np.array(cumsum)
    # ~ 수정

    return selected


def xy2dxdy(xy):
    # 초기값 설정
    dxdy = np.zeros_like(xy)

    # 첫 번째 점은 변위 계산 불가하므로 그대로 사용
    dxdy[0] = xy[0]

    # 두 번째 점부터 변위 계산
    for i in range(1, len(xy)):
        # 현재 좌표와 이전 좌표의 차이 계산
        dx = xy[i][0] - xy[i - 1][0]
        dy = xy[i][1] - xy[i - 1][1]
        # 변위와 pen_state를 변환된 배열에 저장
        dxdy[i] = [dx, dy, xy[i][2]]

    return dxdy


# file_path : .npz file after rdp algorithm
def run(current_index: int, file_name : str):
    p = 8  # number of maximum added strokes
    q = 8  # number of initial strokes
    # Get the directory path of the current script
    npz_file = file_name + '.npz'
    """
    # 설명1: 직전에 UI로부터 p개의 stroke를 입력받은 Input 데이터 ('test')
    # file_path = f"/Users/jungseyoon/Lmser-pix2seq/result/first/*.npz"  # 추가 first, second, ...
    """
    if not os.path.exists(npz_file):
        print("File does not exist.")

    else:
        """
        # data = np.load(file_path, allow_pickle=True, encoding='latin1')  # 추가
        # test_data = data['test']  # 추가
        # 설명2: 설명1과 동일한 데이터를 Lmser-pix2seq/dataset/airplane.npz로 저장 -> 이렇게 해야 inference.py가 input 데이터를 인식할 수 있음 ('test')
        # np.savez('/Users/jungseyoon/Lmser-pix2seq/dataset/airplane.npz', test=test_data)  # 추가
        """

        # file_path의 데이터를 inference.py가 인식 할 수 있는 곳으로 이동
        # original input .npz file after rdp가 file_name에 저장되어 있음

        # subprocess 모듈을 사용하여 Python 스크립트 실행
        # import inference -> call a method run
        inference.run(current_index, npz_file)
        dir_name = file_name
        #  reshaped: 0.npz -> result.npz
        # 설명3: inference.py의 결과 ('x', 'y', 'z')
        # result = np.load('/Users/jungseyoon/Lmser-pix2seq/results/0.0/xyz/airplane/0.npz')
        result = np.load(f'./ai_results/{current_index}/xyz/{dir_name}/0.npz')
        _npy_data = np.stack((result['x'], result['y'], result['z']), axis=1)
        # print(_npy_data.shape)
        reshaped = np.expand_dims(_npy_data, axis=0)
        # sprint("reshaped shape : ", reshaped.shape)
        # 설명4: 설명3의 data reshaped -> 'test'
        # *** np.savez('/Users/jungseyoon/Lmser-pix2seq/dataset/result.npz', test=reshaped)

        #  scale & stroke ordering
        # 설명5: 설명4의 데이터를 load ('test')
        # *** result = np.load("/Users/jungseyoon/Lmser-pix2seq/dataset/result.npz", allow_pickle=True, encoding='latin1')
        # 설명6: 설명2의 데이터를 load ('test')
        # original input .npz file after rdp
        # input 이랑 data 차이가 뭐임...
        input = np.load(npz_file, allow_pickle=True, encoding='latin1')
        # input = np.load("/Users/yoonjiwon/PycharmProjects/demo_1st/lmser/dataset/belt.npz", allow_pickle=True, encoding='latin1')

        result_data = reshaped
        # print("result data type : ", type(result_data))
        # print("result_data shape : ", result_data.shape)
        input_data = input['test'][0]
        input_for_selection = np.expand_dims(input_data, axis=0)
        # print("input data shape : ", input_data.shape)
        # print("input_for_selection shape : ", input_for_selection.shape)
        input_n = len(input_for_selection[0])  # input의 stroke의 개수
        result_n = len(result_data[0])  # result의 stroke의 개수
        # print("input len, result len : ", input_n, result_n)
        if input_n >= result_n:  # input의 stroke 개수 >= output의 stroke 개수
            print("LMSER 실패")

        else:
            if result_n - input_n < p:
                selected_xy = find_nearest_strokes(q, input_for_selection, result_data, result_n - input_n)
            else:
                selected_xy = find_nearest_strokes(q, input_for_selection, result_data, p)
            selected = xy2dxdy(selected_xy) # dx, dy, penstate
            # reshaped = selected.reshape(1, len(selected), 3)

            # input의 stroke와 reshaped의 stroke를 concatenate
            # print("selected shape : ", selected.shape)
            # print("input_data shape : ", input_data.shape)
            output = np.concatenate((input_data, selected), axis = 0)
            # print("output shape : ", output.shape)
            # 설명7: 설명4에서 p개의 stroke를 선택한 다음 이를 설명2와 합친 결과 ('test')
            # np.savez(f'{dir_name}_result.npz', output)
            np.save(file_name+".npy", output)
