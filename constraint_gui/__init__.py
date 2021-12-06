import itertools

from .colors import colors
from typing import Iterable, Callable, Optional

import pyglet
from pyglet.gl import glClearColor
from pyglet.graphics import OrderedGroup
from sympy.solvers import solve
from sympy import Symbol, Eq, lambdify, Expr

WIDGET_WIDTH = Symbol("Ww")
WIDGET_HEIGHT = Symbol("Wh")

WIDGET_X = Symbol("Wx")
WIDGET_Y = Symbol("Wy")

WIDGET_TOP_EDGE = WIDGET_Y + WIDGET_HEIGHT
WIDGET_RIGHT_EDGE = WIDGET_X + WIDGET_WIDTH

RELATIVE_X = Symbol("RELATIVE_X")
RELATIVE_Y = Symbol("RELATIVE_Y")
RELATIVE_WIDTH = Symbol("RELATIVE_WIDTH")
RELATIVE_HEIGHT = Symbol("RELATIVE_HEIGHT")


def color(name: str):
    return colors[name]


# TODO: specify parent_widget in args of constraints
def aspect_constraint(aspect_ration: float = 1):
    return Eq(WIDGET_WIDTH, WIDGET_HEIGHT * aspect_ration)


def self_centered(expr: Expr):
    return expr.subs({
        WIDGET_X: WIDGET_X + WIDGET_WIDTH / 2,
        WIDGET_Y: WIDGET_Y + WIDGET_HEIGHT / 2
    })


def width_percent(factor: float):
    return Eq(WIDGET_WIDTH, RELATIVE_WIDTH * factor)


def height_percent(factor: float):
    return Eq(WIDGET_HEIGHT, RELATIVE_HEIGHT * factor)


def x_percent(factor: float):
    return Eq(WIDGET_X, RELATIVE_WIDTH * factor)


def y_percent(factor: float):
    return Eq(WIDGET_Y, RELATIVE_HEIGHT * factor)


def left_inside(pixels: float = 10):
    return Eq(WIDGET_X, RELATIVE_X + pixels)


def bottom_inside(pixels: float = 10):
    return Eq(WIDGET_Y, RELATIVE_Y + pixels)


def right_inside(pixels: float = 10):
    return Eq(WIDGET_X + WIDGET_WIDTH, RELATIVE_X + RELATIVE_WIDTH - pixels)


def top_inside(pixels: float = 10):
    return Eq(WIDGET_Y + WIDGET_HEIGHT, RELATIVE_Y + RELATIVE_HEIGHT - pixels)


def under(widget: "Widget", pixels: float = 10):
    return Eq(WIDGET_TOP_EDGE, widget.y_expr - pixels)


parent_x_centered = self_centered(Eq(WIDGET_X, RELATIVE_WIDTH / 2))
parent_y_centered = self_centered(Eq(WIDGET_Y, RELATIVE_HEIGHT / 2))


def to(widget: "Widget", constraint: Expr):
    # replaces RELATIVE_* symbols
    return constraint.subs({
        RELATIVE_X: widget.x_expr,
        RELATIVE_Y: widget.y_expr,
        RELATIVE_WIDTH: widget.width_expr,
        RELATIVE_HEIGHT: widget.height_expr
    })


class ConstraintResolutionException(Exception): ...


class RenderException(Exception): ...


class Widget:
    def __init__(self, window: Optional["Window"], master: Optional["Widget"] = None):
        self.x = 0.
        self.y = 0.
        self.width = 0.
        self.height = 0.

        self._x: Callable[[int, int], int] | None = None
        self._y: Callable[[int, int], int] | None = None
        self._width: Callable[[int, int], int] | None = None
        self._height: Callable[[int, int], int] | None = None

        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.is_destroyed = False

        self.master = master
        if self.master:
            self.master.register_child(self)

        self.window_: Window = window
        if self.window_:
            self.window_.register_widget(self)

        self.constraints = []
        self._solutions = []
        self.children: set[Widget] = set()

    def register_child(self, widget: "Widget"):
        self.children.add(widget)

    @property
    def z(self):
        assert self.master is not None, RenderException("No master specified")
        return self.master.z + 1

    @property
    def group(self):
        return OrderedGroup(self.z)

    @property
    def constraints(self):
        return self._constraints

    @constraints.setter
    def constraints(self, constraints: Iterable[Eq | tuple[Eq, set["Widget"]]]):
        """This is very expensive since it needs to solve a system of equations. Ideally, only invoke once."""
        self.depends_on = set()

        self._constraints = []
        for constraint in constraints:
            if isinstance(constraint, tuple):
                constraint, referenced_widgets = constraint
            else:
                referenced_widgets = {}

            if self in referenced_widgets:
                ConstraintResolutionException(f"Can't reference self, you can use attributes of self though: "
                                              f"{constraint!r}")

            # assume constraint is "relative" (for example WIDGET_X references *this* widget's x) to this widget
            # assume all symbols with no specified relation are referencing this widget
            self._constraints.append(self.get_expr(constraint))

            self.depends_on.update(referenced_widgets)

        if self.window_:
            self.window_.resolve_constraints_on_next_frame = True

    @property
    def solutions(self):
        return self._solutions

    @solutions.setter
    def solutions(self, solutions):
        self._solutions = solutions

        args = self.window_.expr_params

        try:
            self._x = lambdify(args, solutions[self.x_expr])
            self._y = lambdify(args, solutions[self.y_expr])
            self._width = lambdify(args, solutions[self.width_expr])
            self._height = lambdify(args, solutions[self.height_expr])
        except KeyError as e:
            raise ConstraintResolutionException("Solutions invalid/insufficient. Couldn't resolve the above variable. "
                                                "Either constraints are to lax or conflict each other.") from e

    def update_self(self):
        self.x = float(self._x(*self.window_.params))
        self.y = float(self._y(*self.window_.params))
        self.width = float(self._width(*self.window_.params))
        self.height = float(self._height(*self.window_.params))

    def get_expr(self, expr):
        """Converts a relative expression, e. g. Eq(WIDGET_WIDTH, WIDGET_HEIGHT) to an absolute expression, e. g.
        Eq(Symbol(Ww_<widget_id>), Symbol(Wh_<widget_id>))"""
        # TODO: add relative constraint function since x and y are absolute now
        return expr.subs({
            WIDGET_X: self.x_expr,
            WIDGET_Y: self.y_expr,
            WIDGET_WIDTH: self.width_expr,
            WIDGET_HEIGHT: self.height_expr
            # TODO: add parent widget??
        })

    @property
    def expr_params(self):
        return self.x_expr, self.y_expr, self.width_expr, self.height_expr

    @property
    def params(self):
        return self.x, self.y, self.width, self.height

    @property
    def x_expr(self):
        return Symbol(f"Wx_{id(self)}")

    @property
    def y_expr(self):
        return Symbol(f"Wy_{id(self)}")

    @property
    def width_expr(self):
        return Symbol(f"Ww_{id(self)}")

    @property
    def height_expr(self):
        return Symbol(f"Wh_{id(self)}")

    @property
    def right_edge(self):
        return self.x + self.width

    @property
    def top_edge(self):
        return self.y + self.height

    @property
    def x_center(self):
        return self.x + self.width / 2

    @property
    def y_center(self):
        return self.y + self.height / 2

    def draw_self(self, batch: pyglet.graphics.Batch):
        ...

    def _on_mouse_motion(self, x, y, dx, dy):
        in_child = False

        for child in self.children:
            # check if cursor is in child
            if child.x < x < child.right_edge and child.y < y < child.top_edge:
                child._on_mouse_motion(x - child.x, y - child.y, dx, dy)
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

    def get_debug_str(self):
        return f"Wx={self.solutions[WIDGET_X]}={self.x:.0f}\n" \
               f"Wy={self.solutions[WIDGET_Y]}={self.y:.0f}\n" \
               f"Ww={self.solutions[WIDGET_WIDTH]}={self.width:.0f}\n" \
               f"Wh={self.solutions[WIDGET_HEIGHT]}={self.height:.0f}\n" \
               f"Mx={self.last_mouse_x}\n" \
               f"My={self.last_mouse_y}"


class Label(Widget):
    def __init__(self, window: "Window", master: Widget | None = None,
                 bg=(255, 255, 255),
                 fg=(22, 22, 22, 255),
                 text="",
                 font_name="consolas",
                 font_size=40,
                 bold=False,
                 italic=False,
                 underline=False,
                 align="CC",
                 dpi=None):
        """

        :arg align In the format (North|Center|South)(West|Center|East)
        """
        super().__init__(window, master)

        self.bg = bg
        self.fg = fg

        self.text = text

        self.font_name = font_name
        self.font_size = font_size

        self.bold = bold
        self.italic = italic
        self.underline = underline

        self.align = align
        self.dpi = dpi

    def draw_self(self, batch: pyglet.graphics.Batch):
        self._ = pyglet.shapes.Rectangle(self.x, self.y, self.width, self.height, color=self.bg,
                                         batch=batch, group=OrderedGroup(0, self.group))

        if self.width <= 0:
            self.width = 1

        self.__ = pyglet.text.Label(text=self.text,
                                    x=self.x,
                                    y={"N": self.top_edge, "C": self.y_center, "S": self.y}[self.align[0]],
                                    width=self.width,
                                    font_name=self.font_name,
                                    font_size=self.font_size,
                                    color=self.fg,
                                    multiline=True,
                                    dpi=self.dpi,
                                    anchor_y={"N": "top", "C": "center", "S": "baseline"}[self.align[0]],
                                    align={"W": "left", "C": "center", "E": "right"}[self.align[1]],
                                    batch=batch, group=OrderedGroup(1, self.group))


class Window(Widget):
    def __init__(self, bg=(255, 255, 255)):
        self.window = pyglet.window.Window(resizable=True)

        self.widgets: set[Widget] = set()

        # Window has no parent Window
        # noinspection PyTypeChecker
        Widget.__init__(self, None)

        self.constraints = [Eq(WIDGET_X, 0),
                            Eq(WIDGET_Y, 0),
                            Eq(WIDGET_WIDTH, self.window.width),
                            Eq(WIDGET_HEIGHT, self.window.height)]

        self.resolve_constraints_on_next_frame = True

        self.bg = bg

        self.window.event("on_draw")(self.loopiter)
        self.window.event("on_mouse_motion")(self._on_mouse_motion)

    @property
    def z(self):
        return 0

    @property
    def bg(self):
        return self._bg

    @bg.setter
    def bg(self, color_: tuple[int, int, int]):
        self.window.switch_to()
        glClearColor(*tuple(val // 255 for val in color_), 255)
        self._bg = color_

    def loopiter(self):
        self.width = self.window.width
        self.height = self.window.height

        self.window.switch_to()
        self.window.clear()
        self.draw()

    def draw(self):
        if self.resolve_constraints_on_next_frame:
            self.solve_constraints()

            self.resolve_constraints_on_next_frame = False

        batch = pyglet.graphics.Batch()

        for widget in self.widgets:
            widget.update_self()
            widget.draw_self(batch)

        batch.draw()

    def solve_constraints(self):
        all_constraints = []

        # add constraints of all widgets
        for widget in self.widgets:
            all_constraints += widget.constraints

        solutions: dict[Symbol: Expr] = solve(
            all_constraints,
            itertools.chain(*[widget.expr_params for widget in self.widgets]),
            dict=True
        )[0]

        for widget in self.widgets:
            widget.solutions = {expr: solutions[expr] for expr in widget.expr_params}

    def register_widget(self, widget: Widget):
        self.widgets.add(widget)
