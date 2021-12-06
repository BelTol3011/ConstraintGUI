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

    button1 = Label(win, left_pane, bg=color("yellow"), bg_on_hover=color("orange"), text="Left", align="CW")
    button1.constraints = [
        top_inside(10),
        left_inside(10),
        right_inside(10),
        height_percent(.10)
    ]

    button2 = Label(win, left_pane, bg=color("yellow"), bg_on_hover=color("orange"), text="Center", align="CC")
    button2.constraints = [
        under(button1, 10),
        left_inside(10),
        right_inside(10),
        height_percent(.10)
    ]

    button3 = Label(win, left_pane, bg=color("yellow"), bg_on_hover=color("orange"), text="Right", align="CE")
    button3.constraints = [
        under(button2, 10),
        left_inside(10),
        right_inside(10),
        height_percent(.10)
    ]

    checkbox1 = CheckBox(win, left_pane, text="CheckBox1")
    checkbox1.constraints = [
        under(button3, 10),
        left_inside(10),
        right_inside(10),
        height_percent(.05)
    ]

    checkbox2 = CheckBox(win, left_pane, text="CheckBox2")
    checkbox2.constraints = [
        under(checkbox1, 10),
        left_inside(10),
        right_inside(10),
        height_percent(.05)
    ]

    checkbox3 = CheckBox(win, left_pane, text="CheckBox3")
    checkbox3.constraints = [
        under(checkbox2, 10),
        left_inside(10),
        right_inside(10),
        height_percent(.05)
    ]

    checkbox4 = CheckBox(win, left_pane, text="CheckBox4")
    checkbox4.constraints = [
        under(checkbox3, 10),
        left_inside(10),
        right_inside(10),
        height_percent(.05)
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

    viscosity_label = Label(win, right_pane, bg=color("orange"), bg_on_hover=color("yellow"))
    viscosity_label.constraints = [
        right_inside(10),
        left_inside(10),
        bottom_inside(10),
        height_percent(.10)
    ]

    pyglet.app.run()


if __name__ == '__main__':
    main()
