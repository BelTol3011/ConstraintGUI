from math import sin

from constraint_gui import *
from constraint_gui.constraints import *
from constraint_gui.test import DebugLabel

win = Window()


width_animation_var = Symbol("w_animation")

label = DebugLabel(win, win, bg=color("black"), bg_on_hover=color("dark green"), fg=color("light blue"), align="NW", font_size=10)
label.constraints = [
    parent_x_centered,
    parent_y_centered,
    height_percent(.5),
    width_percent(width_animation_var)
]

label.animate(width_animation_var, lambda: .5 + sin(time.time()) * .25)

win.mainloop()
