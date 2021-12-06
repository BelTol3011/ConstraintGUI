from constraint_gui import *
from constraint_gui.constraints import *


class MouseTest(Label):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_mouse_motion(self, x, y, dx, dy):
        self.bg = (self.bg[0] + 1 % 256,) * 3


class MouseTestWindow(Window, MouseTest):
    ...


def aligntest():
    win = Window(bg=color("gainsboro"))

    for i, y_align in enumerate("NCS"):
        for j, x_align in enumerate("WCE"):
            align = y_align + x_align
            label = Label(win, win, bg=(128 + (128 // 3 * i), 128 + (128 // 3 * j), 255), text=align, align=align)
            label.constraints = [
                width_percent(1 / 3),
                height_percent(1 / 3),
                y_percent(1 / 3 * i),
                x_percent(1 / 3 * j)
            ]
            win.register_child(label)
    pyglet.app.run()


if __name__ == '__main__':
    aligntest()
