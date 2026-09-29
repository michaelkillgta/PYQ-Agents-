#!/usr/bin/env python3
"""DE ch21 leftover smash: Q122,131,133,137,140,147."""
from ch21_push import push_repairs

REPAIRS = {
    122: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation, $(x^{2} + 1)^{2}\\dfrac{dy}{dx} + 2x(x^{2} + 1)y = 1$ such that $y(0) = 0$. If $\\sqrt{a}\\, y(1) = \\dfrac{\\pi}{32}$, then the value of $a$ is",
        "options": ["$\\dfrac{1}{16}$", "$\\dfrac{1}{2}$", "$\\dfrac{1}{4}$", "$1$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    131: {
        "format": "mcq",
        "body": "Let the solution curve of the differential equation $x\\,dy = \\left(\\sqrt{x^{2} + y^{2}} + y\\right)dx$, $x > 0$, intersect the line $x = 1$ at $y = 0$ and the line $x = 2$ at $y = \\alpha$. Then the value of $\\alpha$ is",
        "options": ["$\\dfrac{1}{2}$", "$\\dfrac{3}{2}$", "$-\\dfrac{3}{2}$", "$\\dfrac{5}{2}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    133: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(x - x^{3})\\,dy = (y + yx^{2} - 3x^{4})\\,dx$, $x > 2$. If $y(3) = 3$, then $y(4)$ is equal to",
        "options": ["$4$", "$12$", "$8$", "$16$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    137: {
        "format": "mcq",
        "body": "A curve amongst the family of curves represented by the differential equation, $(x^{2} - y^{2})\\,dx + 2xy\\,dy = 0$ which passes through $(1, 1)$, is",
        "options": [
            "A circle with centre on the $x$-axis.",
            "A circle with centre on the $y$-axis.",
            "A hyperbola with transverse axis along the $x$-axis.",
            "An ellipse with major axis along the $y$-axis.",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    140: {
        "format": "mcq",
        "body": "Let a smooth curve $y = f(x)$ be such that the slope of the tangent at any point $(x, y)$ on it is directly proportional to $\\left(\\dfrac{-y}{x}\\right)$. If the curve passes through the points $(1, 2)$ and $(8, 1)$, then $\\left|y\\left(\\dfrac{1}{8}\\right)\\right|$ is equal to",
        "options": ["$2\\log_{e} 2$", "$4$", "$1$", "$4\\log_{e} 2$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    147: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(1 + y^{2})e^{\\tan x}\\,dx + \\cos^{2} x\\,(1 + e^{2\\tan x})\\,dy = 0$, $y(0) = 1$. Then $y\\left(\\dfrac{\\pi}{4}\\right)$ is equal to",
        "options": ["$\\dfrac{2}{e}$", "$\\dfrac{2}{e^{2}}$", "$\\dfrac{1}{e}$", "$\\dfrac{1}{e^{2}}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
