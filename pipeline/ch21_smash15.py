#!/usr/bin/env python3
"""DE ch21 leftover smash: Q127,129,130,132,145,149."""
from ch21_push import push_repairs

REPAIRS = {
    127: {
        "format": "mcq",
        "body": "If $\\dfrac{dy}{dx} + \\dfrac{3}{\\cos^{2} x} y = \\dfrac{1}{\\cos^{2} x}$, $x \\in \\left(-\\dfrac{\\pi}{3}, \\dfrac{\\pi}{3}\\right)$, and $y\\left(\\dfrac{\\pi}{4}\\right) = \\dfrac{4}{3}$, then $y\\left(-\\dfrac{\\pi}{4}\\right)$ is equal to",
        "options": ["$\\dfrac{1}{3}$", "$\\dfrac{1}{3} + e^{3}$", "$\\dfrac{1}{3} + e^{6}$", "$-\\dfrac{4}{3}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    129: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\sec^{2} x\\,dx + (e^{2y}\\tan^{2} x + \\tan x)\\,dy = 0$, $0 < x < \\dfrac{\\pi}{2}$, $y\\left(\\dfrac{\\pi}{4}\\right) = 0$. If $y\\left(\\dfrac{\\pi}{6}\\right) = \\alpha$, then $e^{8\\alpha}$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "9",
    },
    130: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be a solution curve of the differential equation, $(1 - x^{2}y^{2})\\,dx = y\\,dx + x\\,dy$. If the line $x = 1$ intersects the curve $y = y(x)$ at $y = 2$ and the line $x = 2$ intersects the curve $y = y(x)$ at $y = \\alpha$, then a value of $\\alpha$ is",
        "options": [
            "$\\dfrac{1 - 3e^{2}}{2(3e^{2} + 1)}$",
            "$\\dfrac{1 + 3e^{2}}{2(3e^{2} - 1)}$",
            "$\\dfrac{3e^{2}}{2(3e^{2} - 1)}$",
            "$\\dfrac{3e^{2}}{2(3e^{2} + 1)}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    132: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(x + 1)y' - y = e^{3x}(x + 1)^{2}$, with $y(0) = \\dfrac{1}{3}$. Then, the point $x = -\\dfrac{4}{3}$ for the curve $y = y(x)$ is",
        "options": [
            "not a critical point",
            "a point of local minima",
            "a point of local maxima",
            "a point of inflection",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    145: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution curve of the differential equation, $(y^{2} - x)\\dfrac{dy}{dx} = 1$, satisfying $y(0) = 1$. This curve intersects the $X$-axis at a point whose abscissa is",
        "options": ["$2 - e$", "$-e$", "$2$", "$2 + e$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    149: {
        "format": "numerical",
        "body": "Let $S = (0, 2\\pi) - \\left\\{\\dfrac{\\pi}{2}, \\dfrac{3\\pi}{4}, \\dfrac{3\\pi}{2}, \\dfrac{7\\pi}{4}\\right\\}$. Let $y = y(x)$, $x \\in S$, be the solution curve of the differential equation $\\dfrac{dy}{dx} = \\dfrac{1}{1 + \\sin 2x}$, $y\\left(\\dfrac{\\pi}{4}\\right) = \\dfrac{1}{2}$. If the sum of abscissas of all the points of intersection of the curve $y = y(x)$ with the curve $y = \\sqrt{2}\\sin x$ is $\\dfrac{k\\pi}{12}$, then $k$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "42",
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
