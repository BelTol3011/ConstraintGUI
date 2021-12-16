import itertools
import time

from pyglet.window.mouse import LEFT

from .colors import color, random_color
from typing import Iterable, Callable, Optional

import pyglet
from pyglet.gl import glClearColor
from pyglet.graphics import OrderedGroup
from sympy.solvers import solve
from sympy import Symbol, Eq, lambdify

WIDGET_WIDTH = Symbol("Ww")
WIDGET_HEIGHT = Symbol("Wh")
WIDGET_X = Symbol("Wx")
WIDGET_Y = Symbol("Wy")

RELATIVE_X = Symbol("Px")
RELATIVE_Y = Symbol("Py")
RELATIVE_WIDTH = Symbol("Pw")
RELATIVE_HEIGHT = Symbol("Ph")


class ConstraintResolutionException(Exception): ...


class RenderException(Exception): ...


class Widget:
    def __init__(self, window: "Window", master: Optional["Widget"] = None):
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

        self._x: Callable[[int, int], int] | None = None
        self._y: Callable[[int, int], int] | None = None
        self._width: Callable[[int, int], int] | None = None
        self._height: Callable[[int, int], int] | None = None

        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.is_destroyed = False
        self.is_mouse_inside = False

        self.master = master
        if self.master:
            self.master.register_child(self)

        self.window_: Window = window
        if self.window_:
            self.window_.register_widget(self)

        self.constraints = []
        self._solutions = {}
        self.children: set[Widget] = set()

        self.needs_update = True
        self.needs_redraw = True

    def register_child(self, widget: "Widget"):
        self.children.add(widget)

    def register_constraint_reeval(self):
        self.needs_update = True

    def register_redraw(self):
        self.needs_redraw = True

        [child.register_redraw() for child in self.children]

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
    def constraints(self, constraints_: Iterable[Eq | tuple[Eq, set["Widget"]]]):
        """This is very expensive since it needs to solve a system of equations. Ideally, only invoke once."""
        self.depends_on = set()

        self._constraints = []
        for constraint in constraints_:
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

        self._x = lambdify(args, solutions[self.x_expr])
        self._y = lambdify(args, solutions[self.y_expr])
        self._width = lambdify(args, solutions[self.width_expr])
        self._height = lambdify(args, solutions[self.height_expr])

    def update_self(self):
        self.x = float(self._x(*self.window_.params))
        self.y = float(self._y(*self.window_.params))
        self.width = float(self._width(*self.window_.params))
        self.height = float(self._height(*self.window_.params))

        self.needs_update = False

    def get_expr(self, expr):
        """Converts a relative expression, e. g. Eq(WIDGET_WIDTH, WIDGET_HEIGHT) to an absolute expression, e. g.
        Eq(Symbol(Ww_<widget_id>), Symbol(Wh_<widget_id>))"""
        expr = expr.subs({
            WIDGET_X: self.x_expr,
            WIDGET_Y: self.y_expr,
            WIDGET_WIDTH: self.width_expr,
            WIDGET_HEIGHT: self.height_expr
        })

        if self.master is not None:
            expr = expr.subs({
                RELATIVE_X: self.master.x_expr,
                RELATIVE_Y: self.master.y_expr,
                RELATIVE_WIDTH: self.master.width_expr,
                RELATIVE_HEIGHT: self.master.height_expr
            })
        return expr

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
    def right_edge_expr(self):
        return self.x_expr + self.width_expr

    @property
    def top_edge_expr(self):
        return self.y_expr + self.height_expr

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

    def draw(self, batch: pyglet.graphics.Batch):
        self.draw_self(batch)

    def get_affected_widget(self, x, y):
        # only invoke event on most top widgets, we don't want covered widgets to also fire
        for child in self.children:
            # check if cursor is in child
            if child.x < x < child.right_edge and child.y < y < child.top_edge:
                return child.get_affected_widget(x, y)

        return self

    def on_mouse_motion(self, x, y, dx, dy):
        ...

    def on_mouse_press(self, x, y, button, modifiers):
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


class Window(Widget):
    def __init__(self, bg=(255, 255, 255)):
        self.window = pyglet.window.Window(800, 450, resizable=True)

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
        # BaseWindow.register_event_type('on_mouse_drag')
        self.window.event("on_mouse_press")(self._on_mouse_press)
        # BaseWindow.register_event_type('on_mouse_release')
        # BaseWindow.register_event_type('on_mouse_scroll')
        self.window.event("on_resize")(self.on_resize)

    @property
    def z(self):
        return 0

    @property
    def bg(self):
        return self._bg

    @bg.setter
    def bg(self, color_: tuple[int, int, int]):
        self.window.switch_to()
        glClearColor(*tuple(val / 255 for val in color_), 255)
        self._bg = color_

    def on_resize(self, width, height):
        self.width = width
        self.height = height

        # need to reevaluate the constraints
        self.register_constraint_reeval()

        # need to redraw all the widgets
        self.register_redraw()

    def loopiter(self):
        t = time.perf_counter()

        self.window.switch_to()

        self.width = self.window.width
        self.height = self.window.height
        self.draw_()

        self.window.set_caption(f"{time.perf_counter() - t:.5f} s")

    def draw_(self):
        if self.resolve_constraints_on_next_frame:
            self.solve_constraints()

            self.resolve_constraints_on_next_frame = False

        if self.needs_redraw:
            self.window.clear()

        batch = pyglet.graphics.Batch()

        for widget in self.widgets:
            if widget.needs_update or self.needs_update:
                widget.needs_update = False
                widget.update_self()

            if widget.needs_redraw or self.needs_redraw:
                widget.needs_redraw = False
                widget.draw(batch)

        batch.draw()

        self.needs_update = False
        self.needs_redraw = False

    def solve_constraints(self):
        all_constraints = []

        if not self.widgets:
            # nothing to solve
            return

        # add constraints of all widgets
        for widget in self.widgets:
            all_constraints += widget.constraints

        _solutions: list[dict[Symbol, Expr]] = solve(
            all_constraints,
            itertools.chain(*[widget.expr_params for widget in self.widgets]),
            dict=True
        )

        try:
            solutions = _solutions[0]
        except IndexError as e:
            raise ConstraintResolutionException(
                "Got no solutions from sympy.solve :(. This is caused by conflicting constraints that can't be "
                "fulfilled at the same time. For example: [..., top_inside(10), top_inside(20)] or "
                "[..., top_inside(10), under(..., 10)]"
            ) from e


        for widget in self.widgets:
            print(f"*** {widget!r} ***")
            try:
                widget.solutions = {expr: solutions[expr] for expr in widget.expr_params}
                for var, expr in widget.solutions.items():
                    print(f" {var} = {expr}")
            except KeyError as e:
                raise ConstraintResolutionException(
                    f"Solutions invalid/insufficient. Couldn't resolve the above variable for widget {widget!r}. "
                    "Either constraints are to lax or conflict each other.") from e

    def register_widget(self, widget: Widget):
        self.widgets.add(widget)

    def _on_mouse_motion(self, x, y, dx, dy):
        # this could be optimized... oh well
        for widget_ in self.widgets:
            if widget_.is_mouse_inside:
                widget_.register_redraw()

            widget_.is_mouse_inside = False

        widget = self.get_affected_widget(x, y)

        widget.register_redraw()
        widget.is_mouse_inside = True
        widget.on_mouse_motion(x, y, dx, dy)

    def _on_mouse_press(self, x, y, button, modifiers):
        widget = self.get_affected_widget(x, y)
        widget.register_redraw()
        widget.on_mouse_press(x, y, button, modifiers)


class Label(Widget):
    def __init__(self, window: Window, master: Widget | None = None,
                 bg=(255, 255, 255), bg_on_hover: tuple[int, int, int] | None = None,
                 fg=(22, 22, 22, 255),
                 text="",
                 font_name="consolas",
                 font_size=30,
                 bold=False,
                 italic=False,
                 underline=False,
                 align="CC",
                 dpi=None):
        """

        :arg align in the format (North|Center|South)(West|Center|East)
        """
        super().__init__(window, master)

        self.bg = bg
        self.bg_on_hover = bg_on_hover
        self.fg = fg

        self.text = text

        self.font_name = font_name
        self.font_size = font_size

        self.bold = bold
        self.italic = italic
        self.underline = underline

        self.align = align
        self.dpi = dpi

    @property
    def background(self):
        return self.bg_on_hover if self.is_mouse_inside and self.bg_on_hover is not None else self.bg

    def draw_self(self, batch: pyglet.graphics.Batch):
        self.bg_rect = pyglet.shapes.Rectangle(self.x, self.y, self.width, self.height, color=self.background,
                                               batch=batch, group=OrderedGroup(self.z))

        self.text_label = pyglet.text.Label(text=self.text,
                                            x=self.x,
                                            y={"N": self.top_edge, "C": self.y_center, "S": self.y}[self.align[0]],
                                            width=self.width,
                                            font_name=self.font_name,
                                            font_size=self.font_size,
                                            color=self.fg,
                                            multiline=True,
                                            dpi=self.dpi,
                                            anchor_y={"N": "top", "C": "center", "S": "bottom"}[self.align[0]],
                                            align={"W": "left", "C": "center", "E": "right"}[self.align[1]],
                                            batch=batch, group=OrderedGroup(self.z + 1))


class CheckBox(Widget):
    def __init__(self, window: "Window", master: Optional["Widget"] = None,
                 on_color=color("green"), off_color=color("dark red"),
                 font_size=20, align="CW", *label_args, **label_kwargs):
        Widget.__init__(self, window, master)

        self.checkbox_label = Label(window, self)
        self.checkbox_label.constraints = [
            aspect_constraint(1),
            left_inside(0),
            top_inside(0),
            bottom_inside(0)
        ]
        self.checkbox_label.on_mouse_press = self.on_mouse_press

        self.text_label = Label(window, self, font_size=font_size, align=align, *label_args, **label_kwargs)
        self.text_label.constraints = [
            top_inside(0),
            bottom_inside(0),
            right_to(self.checkbox_label, 0),
            right_inside(0)
        ]

        self.on_color = on_color
        self.off_color = off_color

        self.status = False

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

        if status:
            self.checkbox_label.bg = self.on_color
        else:
            self.checkbox_label.bg = self.off_color

    def on_mouse_press(self, x, y, button, modifiers):
        if button != LEFT:
            return
        self.status = not self.status


from .constraints import *
