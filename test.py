from constraint_gui import *


def main():
    win = Window(bg=color("gainsboro"))

    left_pane = Label(win, win, bg=color("dark grey"))
    left_pane.constraints = [
        to(win, left_inside(10)),
        to(win, top_inside(10)),
        to(win, bottom_inside(10)),
        to(win, width_percent(.20)),
    ]

    button1 = Label(win, left_pane, bg=color("yellow"), text="Left")
    button1.constraints = [
        to(left_pane, top_inside(10)),
        to(left_pane, left_inside(10)),
        to(left_pane, right_inside(10)),
        to(left_pane, height_percent(.10))
    ]

    button2 = Label(win, left_pane, bg=color("yellow"), text="Center")
    button2.constraints = [
        under(button1, 10),
        to(left_pane, left_inside(10)),
        to(left_pane, right_inside(10)),
        to(left_pane, height_percent(.10))
    ]

    pyglet.app.run()


if __name__ == '__main__':
    main()
