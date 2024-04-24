import tkinter as tk
import numpy as np
import argparse

class MousePainter:
    def __init__(self, args):
        self.root = tk.Tk()
        self.root.title("Drawing with Mouse")

        self.last_x = 0
        self.last_y = 0
        self.is_pressed = False
        self.deltas = []

        self.canvas_init()

    def canvas_init(self):
        self.canvas = tk.Canvas(self.root, width=256, height=256, bg="white")
        self.canvas.pack()

        self.canvas.bind("<Button-1>", self.start_paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.exit_button = tk.Button(self.root, text="Exit", command=self.exit_application)
        self.exit_button.pack()

        self.save_button = tk.Button(self.root, text="Save Deltas", command=self.save_deltas)
        self.save_button.pack()

    def exit_application(self):
        self.root.quit()

    def start_paint(self, event):
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        self.deltas.append((dx, dy, not self.is_pressed))
        self.last_x, self.last_y = event.x, event.y
        self.is_pressed = True

    def stop_paint(self, event):
        self.is_pressed = False

    def paint(self, event):
        x, y = event.x, event.y
        dx = x - self.last_x
        dy = y - self.last_y
        self.deltas.append((dx, dy, not self.is_pressed))
        if self.is_pressed:
            self.canvas.create_line((self.last_x, self.last_y, x, y), fill="black", width=2)
        self.last_x, self.last_y = x, y

    def save_deltas(self):
        np.save(args.savefile_name, np.array(self.deltas))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Evaluation input filepaths
    parser.add_argument('--savefile_name', type=str, help='set output file name', default='mouse_deltas.npy')
    args = parser.parse_args()

    painter = MousePainter(args)
    painter.run()