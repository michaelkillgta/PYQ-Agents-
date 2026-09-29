#!/usr/bin/env python3
"""DE ch21 batch 4: Q50,62,64,66,67,70."""
from ch21_push import push_repairs

REPAIRS = {
    50: {
        "format": "mcq",
        "body": "The solution curve of the differential equation $(1 + e^{-x})(1 + y^{2})\\,\\dfrac{dy}{dx} = y^{2}$ which passes through the point $(0, 1)$, is",
        "options": [
            "$y^{2} + 1 = y\\left(\\log_{e}\\left(\\dfrac{1 + e^{-x}}{2}\\right) + 2\\right)$",
            "$y^{2} + 1 = y\\left(\\log_{e}\\left(\\dfrac{1 + e^{x}}{2}\\right) + 2\\right)$",
            "$y^{2} = 1 + y\\log_{e}\\left(\\dfrac{1 + e^{x}}{2}\\right)$",
            "$y^{2} = 1 + y\\log_{e}\\left(\\dfrac{1 + e^{-x}}{2}\\right)$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    62: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(3y^{2} - 5x^{2})y\\,dx + 2x(x^{2} - y^{2})\\,dy = 0$ such that $y(1) = 1$. Then $|(y(2))^{3} - 12y(2)|$ is equal to",
        "options": ["$64$", "$32\\sqrt{2}$", "$32$", "$16\\sqrt{2}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    64: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} = \\dfrac{4y^{3} + 2yx^{2}}{3xy^{2} + x^{3}}$, $y(1) = 1$. If for some $n \\in \\mathbb{N}$, $y(2) \\in [n - 1, n)$, then $n$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    66: {
        "format": "mcq",
        "body": "Let $g$ be a differentiable function such that $\\displaystyle\\int_{0}^{x} g(t)\\,dt = x - \\int_{0}^{x} t g(t)\\,dt$, $x \\ge 0$ and let $y = y(x)$ satisfy the differential equation $\\dfrac{dy}{dx} - y\\tan x = 2(x + 1)\\sec x\\, g(x)$, $x \\in [0, \\pi/2)$. If $y(0) = 0$, then $y(\\pi/3)$ is equal to",
        "options": [
            "$\\dfrac{2\\pi}{3\\sqrt{3}}$",
            "$\\dfrac{4\\pi}{3}$",
            "$\\dfrac{2\\pi}{3}$",
            "$\\dfrac{4\\pi}{3\\sqrt{3}}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    67: {
        "format": "mcq",
        "body": "Let $f : [0, \\infty) \\to \\mathbb{R}$ be a differentiable function such that $f(x) = 1 - 2x + \\int_{0}^{x} e^{x-t} f(t)\\,dt$ for all $x \\in [0, \\infty)$. Then the area of the region bounded by $y = f(x)$ and the coordinate axes is",
        "options": ["$\\sqrt{5}$", "$\\dfrac{1}{2}$", "$\\sqrt{2}$", "$2$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    70: {
        "format": "mcq",
        "body": "Let $x = x(y)$ be the solution of the differential equation $y^{2}\\,dx + \\left(x - \\dfrac{1}{y}\\right)dy = 0$. If $x(1) = 1$, then $x(1/2)$ is",
        "options": ["$\\dfrac{1}{2} + e$", "$3 + e$", "$3 - e$", "$\\dfrac{3}{2} + e$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
