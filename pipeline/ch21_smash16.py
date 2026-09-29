#!/usr/bin/env python3
"""DE ch21 leftover smash: Q162,164,181,186."""
from ch21_push import push_repairs

REPAIRS = {
    162: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} + 2y\\sec^{2} x = 2\\sec^{2} x + 3\\tan x \\cdot \\sec^{2} x$ such that $y(0) = \\dfrac{5}{4}$. Then $12\\left(y\\left(\\dfrac{\\pi}{4}\\right) - e^{-2}\\right)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "21",
    },
    164: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(x^{2} + 1)y' - 2xy = (x^{4} + 2x^{2} + 1)\\cos x$, $y(0) = 1$. Then $\\int_{-3}^{3} y(x)\\,dx$ is",
        "options": ["$24$", "$36$", "$30$", "$18$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    181: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be a solution curve of the differential equation $(y + 1)\\tan^{2} x\\,dx + \\tan x\\,dy + y\\,dx = 0$, $x \\in \\left(0, \\dfrac{\\pi}{2}\\right)$. If $\\displaystyle\\lim_{x \\to 0^{+}} xy(x) = 1$, then the value of $y\\left(\\dfrac{\\pi}{4}\\right)$ is",
        "options": [
            "$\\dfrac{\\pi}{4} + 1$",
            "$\\dfrac{\\pi}{4} - 1$",
            "$\\dfrac{\\pi}{4}$",
            "$-\\dfrac{\\pi}{4}$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    186: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation, $xy' - y = x^{2}(x\\cos x + \\sin x)$, $x > 0$. If $y(\\pi) = \\pi$, then $y''\\left(\\dfrac{\\pi}{2}\\right) + y\\left(\\dfrac{\\pi}{2}\\right)$ is equal to",
        "options": [
            "$2 + \\dfrac{\\pi}{2}$",
            "$1 + \\dfrac{\\pi}{2} + \\dfrac{\\pi^{2}}{4}$",
            "$2 + \\dfrac{\\pi}{2} + \\dfrac{\\pi^{2}}{4}$",
            "$1 + \\dfrac{\\pi}{2}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
