import numpy as np
import tensorflow as tf
import subprocess
import os


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


def find_first_stroke(input):
    # np.where 함수는 조건을 만족하는 요소의 인덱스를 반환합니다.
    # points 배열의 모든 요소 중에서 세 번째 열의 값이 1인 첫 번째 요소의 인덱스를 찾습니다.
    # 이때, ravel() 함수를 사용하여 다차원 배열을 1차원 배열로 펼칩니다.
    in_indices = np.where(in_points[:, :, 2].ravel() == 1)[0]
    input_index = in_indices[0]
    input_1 = input[:, :(input_index + 1):, :]
    return input_1


def calculate_distance(p1, p2):
    w = (p1[0] - p2[0]) * (p1[0] - p2[0])
    h = (p1[1] - p2[1]) * (p1[1] - p2[1])
    return (w + h) ** (0.5)


def find_nearest_strokes(input, result, stroke_n):
    result_data = result['test']
    input_data = input['test']

    input_n = len(input_data[0])  # input stroke의 개수
    result_n = len(result_data[0])  # output stroke의 개수

    selected = result_data[:, input_n:, :]

    # scaling ~
    input_1 = input_data[:, :q, :]
    result_1 = result_data[:, :q, :]

    factor_x, factor_y = calculate_proportion(input_1, result_1)

    selected[:, :, 0] *= factor_x
    selected[:, :, 1] *= factor_y

    selected = np.round(selected).astype(int)
    # ~ scaling

    # [dx, dy, pen_state] -> [x, y, pen_state] ~
    points = selected[0]
    dxdy = points[:, :2]  # (dx, dy) 부분
    pen = points[:, 2:]  # pen_state 부분

    # dxdy[:, 1] = - dxdy[:, 1]
    xy = np.cumsum(dxdy, axis=0)

    cumsum = np.concatenate((xy, pen), axis=-1)

    start_point = np.array([0, 0, 0])
    cumsum = np.vstack((start_point, cumsum))
    # ~ [dx, dy, pen_state] -> [x, y, pen_state]

    # sorting ~
    distances = [(calculate_distance([0, 0], [point[0], point[1]]), idx) for idx, point in enumerate(cumsum[1:])]

    distances.sort()  # 거리가 가까운 순으로 정렬
    indices = [idx for _, idx in distances[:stroke_n]]  # 가장 가까운 점들의 인덱스 추출

    selected = np.array([cumsum[idx + 1] for idx in indices])
    # ~ sorting

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


def run():
    p = 4  # number of maximum added strokes
    q = 4  # number of initial strokes

    file_path = f"/Users/jungseyoon/Lmser-pix2seq/result/first/*.npz"  # 추가 first, second, ...

    if os.path.exists(file_path):  # 추가
        data = np.load(file_path, allow_pickle=True, encoding='latin1')  # 추가
        test_data = data['test']  # 추가
        np.savez('/Users/jungseyoon/Lmser-pix2seq/dataset/airplane.npz', test=test_data)  # 추가

        #  subprocess 모듈을 사용하여 Python 스크립트 실행
        subprocess.run(["python", "inference.py"])

        #  reshaped: 0.npz -> result.npz
        result = np.load('/Users/jungseyoon/Lmser-pix2seq/results/0.0/xyz/airplane/0.npz')
        _npy_data = np.stack((result['x'], result['y'], result['z']), axis=1)
        reshaped = np.expand_dims(_npy_data, axis=0)
        np.savez('/Users/jungseyoon/Lmser-pix2seq/dataset/result.npz', test=reshaped)

        #  스케일링 및 stroke ordering
        result = np.load("/Users/jungseyoon/Lmser-pix2seq/dataset/result.npz", allow_pickle=True, encoding='latin1')
        input = np.load("/Users/jungseyoon/Lmser-pix2seq/dataset/airplane.npz", allow_pickle=True, encoding='latin1')
        result_data = result['test']
        input_data = input['test']

        input_n = len(input_data[0])  # input의 stroke의 개수
        result_n = len(result_data[0])  # result의 stroke의 개수

        if input_n >= result_n:  # input의 stroke 개수 >= output의 stroke 개수
            print("LMSER 실패")
        else:
            if result_n - input_n < p:
                selected_xy = find_nearest_strokes(input, result, result_n - input_n)
            else:
                selected_xy = find_nearest_strokes(input, result, p)
            selected = xy2dxdy(selected_xy)
            reshaped = selected.reshape(1, len(selected), 3)

            # 마지막 요소의 pen_state를 1로 바꾸기
            # selected_points[0][len(selected_points[0]) - 1][2] = 1

            # input의 stroke와 reshaped의 stroke를 concatenate
            output = np.concatenate((input_data, reshaped), axis=1)

            np.savez(f"/Users/jungseyoon/Lmser-pix2seq/result/second/***.npz", test=output)  # second, third, ...

    else:  # 추가
        print("File does not exist.")
