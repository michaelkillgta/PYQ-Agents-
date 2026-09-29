#!/usr/bin/env python3
"""AoD ch17 held batch 4: Q52-57."""
from ch17_push import push_repairs

REPAIRS = {
    52: {
        "format": "mcq",
        "body": "If the tangent to the curve $y = x + \\sin y$ at a point $(a, b)$ is parallel to the line joining $\\left(0, \\dfrac{3}{2}\\right)$ and $\\left(\\dfrac{1}{2}, 2\\right)$, then",
        "options": [
            "$b = a$",
            "$|b - a| = 1$",
            "$|a + b| = 1$",
            "$b = \\dfrac{\\pi}{2} + a$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    53: {
        "format": "numerical",
        "body": "If the tangent to the curve $y = e^{x}$ at a point $(c, e^{c})$ and the normal to the parabola $y^{2} = 4x$ at the point $(1, 2)$ intersect at the same point on the $x$-axis, then the value of $c$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    54: {
        "format": "numerical",
        "body": "If the lines $x + y = a$ and $x - y = b$ touch the curve $y = x^{2} - 3x + 2$ at the points where the curve intersects the $x$-axis, then $\\dfrac{a}{b}$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "0.5",
    },
    55: {
        "format": "mcq",
        "body": "If the tangent to the curve $y = f(x) = x \\log_{e} x$, $(x > 0)$ at a point $(c, f(c))$ is parallel to the line-segment joining the points $(1, 0)$ and $(e, e)$, then $c$ is equal to",
        "options": [
            "$\\dfrac{e - 1}{e}$",
            "$e^{\\left(\\dfrac{e}{e - 1}\\right)}$",
            "$e^{\\left(\\dfrac{1}{1 - e}\\right)}$",
            "$\\dfrac{1}{e - 1}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    56: {
        "format": "numerical",
        "body": "Let the normal at a point $P$ on the curve $y^{2} - 3x^{2} + y + 10 = 0$ intersect the $y$-axis at $\\left(0, \\dfrac{3}{2}\\right)$. If $m$ is the slope of the tangent at $P$ to the curve, then $|m|$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    57: {
        "format": "mcq",
        "body": "If the tangent to the curve, $y = x^{3} + ax - b$ at the point $(1, -5)$ is perpendicular to the line, $-x + y + 4 = 0$, then which one of the following points lies on the curve?",
        "options": ["$(2, -2)$", "$(2, -1)$", "$(-2, 1)$", "$(-2, 2)$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
