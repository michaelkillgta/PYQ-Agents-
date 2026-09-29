#!/usr/bin/env python3
"""AoD ch17 held batch 1: Q3-8."""
from ch17_push import push_repairs

REPAIRS = {
    3: {
        "format": "numerical",
        "body": "Let the quadratic curve passing through the point $(-1, 0)$ and touching the line $y = x$ at $(1, 1)$ be $y = f(x)$. Then the $x$-intercept of the normal to the curve at the point $(\\alpha, \\alpha + 1)$ in the first quadrant is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "11",
    },
    4: {
        "format": "numerical",
        "body": "If the equation of the normal to the curve $y = \\dfrac{x - a}{(x + b)(x - 2)}$ at the point $(1, -3)$ is $x - 4y = 13$ then the value of $a + b$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    5: {
        "format": "mcq",
        "body": "If the tangent at the point $(x_{1}, y_{1})$ on the curve $y = x^{3} + 3x^{2} + 5$ passes through the origin, then $(x_{1}, y_{1})$ does NOT lie on the curve",
        "options": [
            "$x^{2} + \\dfrac{y^{2}}{81} = 2$",
            "$\\dfrac{y^{2}}{9} - x^{2} = 8$",
            "$y = 4x^{2} + 5$",
            "$\\dfrac{x}{3} - y^{2} = 2$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    6: {
        "format": "mcq",
        "body": "For which of the following curves, the line $x + \\sqrt{3} y = 2\\sqrt{3}$ is the tangent at the point $\\left(\\dfrac{3\\sqrt{3}}{2}, \\dfrac{1}{2}\\right)$",
        "options": [
            "$2x^{2} - 18y^{2} = 9$",
            "$y^{2} = \\dfrac{1}{6\\sqrt{3}} x$",
            "$x^{2} + 9y^{2} = 9$",
            "$x^{2} + y^{2} = 7$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    7: {
        "format": "mcq",
        "body": "If the curve $y = ax^{2} + bx + c$, $x \\in R$, passes through the point $(1, 2)$ and the tangent line to this curve at origin is $y = x$, then the possible values of $a$, $b$, $c$ are",
        "options": [
            "$a = -1$, $b = 1$, $c = 1$",
            "$a = 1$, $b = 0$, $c = 1$",
            "$a = 1$, $b = 1$, $c = 0$",
            "$a = \\dfrac{1}{2}$, $b = \\dfrac{1}{2}$, $c = 1$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    8: {
        "format": "mcq",
        "body": "The shortest distance between the line $x - y = 1$ and the curve $x^{2} = 2y$ is",
        "options": ["$\\dfrac{1}{2}$", "$\\dfrac{1}{\\sqrt{2}}$", "$\\dfrac{1}{2\\sqrt{2}}$", "$0$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
