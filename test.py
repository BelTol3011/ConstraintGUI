from constraint_gui import *
from constraint_gui.constraints import *


def main():
    win = Window(bg=color("gainsboro"))

    left_pane = Label(win, win, bg=color("dark grey"))
    left_pane.constraints = [
        left_inside(10),
        top_inside(10),
        bottom_inside(10),
        width_percent(.20)
    ]

    button1 = Label(win, left_pane, bg=color("yellow"), text="Left", align="CW")
    button1.constraints = [
        top_inside(10),
        left_inside(10),
        right_inside(10),
        height_percent(.10)
    ]

    button2 = Label(win, left_pane, bg=color("yellow"), text="Center", align="CC")
    button2.constraints = [
        under(button1, 10),
        left_inside(10),
        right_inside(10),
        height_percent(.10)
    ]

    button3 = Label(win, left_pane, bg=color("yellow"), text="Right", align="CE")
    button3.constraints = [
        under(button2, 10),
        left_inside(10),
        right_inside(10),
        height_percent(.10)
    ]

    # the checkboxes go here

    right_pane = Label(win, win, bg=color("dark grey"))
    right_pane.constraints = [
        right_inside(10),
        top_inside(10),
        bottom_inside(10),
        width_percent(.20)
    ]

    # scrollbars go here

    viscosity_label = Label(win, right_pane, bg=color("orange"))
    viscosity_label.constraints = [
        right_inside(10),
        left_inside(10),
        bottom_inside(10),
        height_percent(.10)
    ]

    pyglet.app.run()


if __name__ == '__main__':
    main()
