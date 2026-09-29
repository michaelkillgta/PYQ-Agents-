#!/usr/bin/env python3
"""DE ch21 leftover smash: Q9,13,22,34,77,80."""
from ch21_push import push_repairs

REPAIRS = {
    9: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation, $\\dfrac{2 + \\sin x}{y + 1} \\cdot \\dfrac{dy}{dx} = -\\cos x$, $y > 0$, $y(0) = 1$. If $y(\\pi) = a$ and $\\dfrac{dy}{dx}$ at $x = \\pi$ is $b$, then the ordered pair $(a, b)$ is equal to",
        "options": ["$(2, \\dfrac{3}{2})$", "$(1, -1)$", "$(1, 1)$", "$(2, 1)$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    13: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} + 3(\\tan^{2} x)y + 3y = \\sec^{2} x$, $y(0) = \\dfrac{1}{3} + e^{3}$. Then $y\\left(\\dfrac{\\pi}{4}\\right)$ is equal to",
        "options": ["$\\dfrac{2}{3}$", "$\\dfrac{4}{3}$", "$\\dfrac{4}{3} + e^{3}$", "$\\dfrac{2}{3} + e^{3}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    22: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation, $\\dfrac{dy}{dx} + 2y\\tan x = \\sin x$, $y\\left(\\dfrac{\\pi}{3}\\right) = 0$, then the maximum value of the function $y(x)$ over $R$ is equal to",
        "options": ["$8$", "$\\dfrac{1}{2}$", "$-\\dfrac{15}{4}$", "$\\dfrac{1}{8}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    34: {
        "format": "mcq",
        "body": "If the solution $y = y(x)$ of the differential equation $(x^{4} + 2x^{3} + 3x^{2} + 2x + 2)\\,dy - (2x^{2} + 2x + 3)\\,dx = 0$ satisfies $y(-1) = -\\dfrac{\\pi}{4}$, then $y(0)$ is equal to",
        "options": ["$\\dfrac{\\pi}{2}$", "$-\\dfrac{\\pi}{2}$", "$0$", "$\\dfrac{\\pi}{4}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    77: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation $\\dfrac{dy}{dx} + 2y = \\sin(2x)$, $y(0) = \\dfrac{3}{4}$, then $y\\left(\\dfrac{\\pi}{8}\\right)$ is equal to",
        "options": ["$e^{\\pi/8}$", "$e^{\\pi/4}$", "$e^{-\\pi/4}$", "$e^{-\\pi/8}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    80: {
        "format": "mcq",
        "body": "A function $y = f(x)$ satisfies $f(x)\\sin 2x + \\sin x - (1 + \\cos^{2} x)f'(x) = 0$ with condition $f(0) = 0$. Then $f\\left(\\dfrac{\\pi}{2}\\right)$ is equal to",
        "options": ["$1$", "$0$", "$-1$", "$2$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
