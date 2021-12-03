from typing import Any

import pyglet
from pyglet.gl import glClearColor
from pyglet.graphics import OrderedGroup
from sympy.solvers import solve
from sympy import Symbol, Eq, lambdify, Expr

PARENT_WIDTH = Symbol("Pw")
PARENT_HEIGHT = Symbol("Ph")

WIDGET_WIDTH = Symbol("Ww")
WIDGET_HEIGHT = Symbol("Wh")

WIDGET_X = Symbol("Wx")
WIDGET_Y = Symbol("Wy")


def aspect_constraint(aspect_ration: float = 1):
    return Eq(WIDGET_WIDTH, WIDGET_HEIGHT * aspect_ration)


def self_centered(expr: Expr):
    return expr.subs({
        WIDGET_X: WIDGET_X + WIDGET_WIDTH / 2,
        WIDGET_Y: WIDGET_Y + WIDGET_HEIGHT / 2
    })


def left_inside(pixels: float = 20):
    return Eq(WIDGET_X, pixels)


def bottom_inside(pixels: float = 20):
    return Eq(WIDGET_Y, pixels)


def right_inside(pixels: float = 20):
    return Eq(WIDGET_X + WIDGET_WIDTH, PARENT_WIDTH - pixels)


def top_inside(pixels: float = 20):
    return Eq(WIDGET_Y + WIDGET_HEIGHT, PARENT_HEIGHT - pixels)


parent_x_centered = self_centered(Eq(WIDGET_X, PARENT_WIDTH / 2))
parent_y_centered = self_centered(Eq(WIDGET_Y, PARENT_HEIGHT / 2))


class ConstraintResolutionException(Exception): ...


class Widget:
    def __init__(self, constraints: list[Eq] = None):
        self.constraints = [Eq(WIDGET_X, 0),
                            Eq(WIDGET_Y, 0),
                            Eq(WIDGET_WIDTH, PARENT_WIDTH),
                            Eq(WIDGET_HEIGHT, PARENT_HEIGHT)] if constraints is None else constraints
        self.x = 0.
        self.y = 0.
        self.width = 0.
        self.height = 0.

        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.children: list[Widget] = []
        self.is_destroyed: bool = False

    @property
    def constraints(self):
        return self._constraints

    @constraints.setter
    def constraints(self, constraints: Eq):
        """This is very expensive since it needs to solve a system of equations. Ideally, only use once."""
        self._constraints = constraints
        self.solutions = solve(self._constraints, WIDGET_X, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT)

        args = PARENT_WIDTH, PARENT_HEIGHT
        try:
            self._x = lambdify(args, self.solutions[WIDGET_X])
            self._y = lambdify(args, self.solutions[WIDGET_Y])
            self._width = lambdify(args, self.solutions[WIDGET_WIDTH])
            self._height = lambdify(args, self.solutions[WIDGET_HEIGHT])
        except KeyError as e:
            raise ConstraintResolutionException("Couldn't resolve the above variable. Either constraints are to lax or "
                                                "conflict each other.") from e

    def update_self(self, parent: "Widget"):
        self.x = self._x(parent.width, parent.height) + parent.x
        self.y = self._y(parent.width, parent.height) + parent.y
        self.width = self._width(parent.width, parent.height)
        self.height = self._height(parent.width, parent.height)

    @property
    def top_edge(self):
        return self.y + self.height

    @property
    def right_edge(self):
        return self.x + self.width

    def update_children(self):
        for i, child in enumerate(self.children):
            if child.is_destroyed:
                del self.children[i]

            child.update(self)

    def update(self, parent: "Widget"):
        self.update_self(parent)
        self.update_children()

    def draw_self(self, batch: pyglet.graphics.Batch, group: pyglet.graphics.Group):
        ...

    def draw(self, batch: pyglet.graphics.Batch, z=0):
        self.draw_self(batch, OrderedGroup(z))

        for child in self.children:
            child.draw(batch, z + 1)

    def _on_mouse_motion(self, x, y, dx, dy):
        in_child = False

        for child in self.children:
            # check if cursor is in child
            if child.x < x < child.right_edge and child.y < y < child.top_edge:
                child._on_mouse_motion(x, y, dx, dy)
                in_child = True

        # only invoke event on most top widgets, we don't want covered widgets to also fire
        if not in_child:
            self.last_mouse_x = x
            self.last_mouse_y = y
            self.on_mouse_motion(x, y, dx, dy)

    def on_mouse_motion(self, x, y, dx, dy):
        ...

    def destroy(self):
        self.is_destroyed = True

    def register_child(self, widget: "Widget"):
        self.children.append(widget)

    def get_debug_str(self):
        return f"Wx={self.solutions[WIDGET_X]}={self.x:.0f}\n" \
               f"Wy={self.solutions[WIDGET_Y]}={self.y:.0f}\n" \
               f"Ww={self.solutions[WIDGET_WIDTH]}={self.width:.0f}\n" \
               f"Wh={self.solutions[WIDGET_HEIGHT]}={self.height:.0f}\n" \
               f"Mx={self.last_mouse_x}\n" \
               f"My={self.last_mouse_y}"


class Label(Widget):
    _: Any
    __: Any

    def __init__(self,
                 bg=(255, 255, 255),
                 fg=(22, 22, 22, 255),
                 text: str = None,
                 font_name="fira code",
                 font_size=None,
                 bold=False,
                 italic=False,
                 anchor_x="left",
                 anchor_y="top",
                 align="left",
                 dpi=None):
        super().__init__()

        self.bg = bg
        self.fg = fg
        self.text = text

        self.font_name = font_name
        self.font_size = font_size
        self.bold = bold
        self.italic = italic
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.align = align
        self.dpi = dpi

    def draw_self(self, batch: pyglet.graphics.Batch, group: pyglet.graphics.Group):
        self._ = pyglet.shapes.Rectangle(self.x, self.y, self.width, self.height, color=self.bg,
                                         batch=batch, group=OrderedGroup(0, group))

        self.__ = pyglet.text.Label(self.text if self.text is not None else self.get_debug_str(),
                                    color=self.fg,
                                    x=self.x,
                                    y=self.top_edge,
                                    width=self.width,
                                    height=self.height,
                                    font_name=self.font_name,
                                    font_size=self.font_size,
                                    bold=self.bold,
                                    italic=self.italic,
                                    anchor_x=self.anchor_x,
                                    anchor_y=self.anchor_y,
                                    align=self.align,
                                    dpi=self.dpi,
                                    multiline=True,
                                    batch=batch, group=OrderedGroup(1, group))


class Window(Widget):
    def __init__(self, bg=(11, 11, 11, 255)):
        Widget.__init__(self)

        self.window = pyglet.window.Window(resizable=True)

        self.bg = bg

        self.window.event("on_draw")(self.loopiter)
        self.window.event("on_mouse_motion")(self._on_mouse_motion)

    @property
    def bg(self):
        return self._bg

    @bg.setter
    def bg(self, color):
        self.window.switch_to()
        glClearColor(*tuple(val / 255 for val in color))
        self._bg = color

    def loopiter(self):
        self.width = self.window.width
        self.height = self.window.height

        self.update_children()

        batch = pyglet.graphics.Batch()
        self.draw(batch)

        self.window.switch_to()
        self.window.clear()
        batch.draw()


def main():
    win = Window()

    mywidget = Label()
    mywidget.constraints = [
        parent_x_centered,
        top_inside(20),
        Eq(WIDGET_HEIGHT, PARENT_HEIGHT * .20),
        aspect_constraint(2),
    ]

    leftpane = Label(bg=(255, 50, 50))
    leftpane.constraints = [
        left_inside(20),
        top_inside(20),
        bottom_inside(20),
        Eq(WIDGET_WIDTH, PARENT_WIDTH * .20),
    ]
    win.register_child(leftpane)
    win.register_child(mywidget)

    pyglet.app.run()


if __name__ == '__main__':
    main()
