from sympy import Eq, Expr, Symbol

from . import WIDGET_X, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT, \
    RELATIVE_X, RELATIVE_Y, RELATIVE_WIDTH, RELATIVE_HEIGHT, \
    Widget

WIDGET_TOP_EDGE = WIDGET_Y + WIDGET_HEIGHT
WIDGET_RIGHT_EDGE = WIDGET_X + WIDGET_WIDTH


def self_centered(expr: Expr):
    return expr.subs({
        WIDGET_X: WIDGET_X + WIDGET_WIDTH / 2,
        WIDGET_Y: WIDGET_Y + WIDGET_HEIGHT / 2
    })


def aspect_constraint(aspect_ration: float | Symbol = 1):
    return Eq(WIDGET_WIDTH, WIDGET_HEIGHT * aspect_ration)


def width_percent(factor: float | Symbol):
    return Eq(WIDGET_WIDTH, RELATIVE_WIDTH * factor)


def height_percent(factor: float | Symbol):
    return Eq(WIDGET_HEIGHT, RELATIVE_HEIGHT * factor)


def x_percent(factor: float | Symbol):
    return Eq(WIDGET_X, RELATIVE_WIDTH * factor)


def y_percent(factor: float | Symbol):
    return Eq(WIDGET_Y, RELATIVE_HEIGHT * factor)


def left_inside(pixels: float | Symbol = 10):
    return Eq(WIDGET_X, RELATIVE_X + pixels)


def bottom_inside(pixels: float | Symbol = 10):
    return Eq(WIDGET_Y, RELATIVE_Y + pixels)


def right_inside(pixels: float | Symbol = 10):
    return Eq(WIDGET_X + WIDGET_WIDTH, RELATIVE_X + RELATIVE_WIDTH - pixels)


def top_inside(pixels: float | Symbol = 10):
    return Eq(WIDGET_Y + WIDGET_HEIGHT, RELATIVE_Y + RELATIVE_HEIGHT - pixels)


def over(widget: Widget, pixels: float | Symbol = 10):
    return Eq(WIDGET_Y, widget.top_edge + pixels)


def under(widget: Widget, pixels: float | Symbol = 10):
    return Eq(WIDGET_TOP_EDGE, widget.y_expr - pixels)


def right_to(widget: Widget, pixels: float | Symbol = 10):
    return Eq(WIDGET_X, widget.right_edge_expr + pixels)


def left_to(widget: Widget, pixels: float | Symbol = 10):
    return Eq(WIDGET_RIGHT_EDGE, widget.x - pixels)


parent_x_centered = self_centered(Eq(WIDGET_X, RELATIVE_WIDTH / 2))
parent_y_centered = self_centered(Eq(WIDGET_Y, RELATIVE_HEIGHT / 2))


def to(widget: Widget, constraint: Expr):
    # replaces RELATIVE_* symbols
    return constraint.subs({
        RELATIVE_X: widget.x_expr,
        RELATIVE_Y: widget.y_expr,
        RELATIVE_WIDTH: widget.width_expr,
        RELATIVE_HEIGHT: widget.height_expr
    })
