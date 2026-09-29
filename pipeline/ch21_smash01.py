#!/usr/bin/env python3
"""DE ch21 smash batch 1: Q18,101,109,120,128."""
from ch21_push import push_repairs

REPAIRS = {
    18: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution curve of the differential equation $\\dfrac{dy}{dx} + y\\tan x = x\\sec x$, $0 \\le x \\le \\pi/3$, $y(0) = 1$, then $y(\\pi/6)$ is equal to",
        "options": [
            "$\\dfrac{\\pi}{12} - \\dfrac{\\sqrt{3}}{2}\\log_{e}\\left(\\dfrac{2}{e\\sqrt{3}}\\right)$",
            "$\\dfrac{\\pi}{12} + \\dfrac{\\sqrt{3}}{2}\\log_{e}\\left(\\dfrac{2\\sqrt{3}}{e}\\right)$",
            "$\\dfrac{\\pi}{12} - \\dfrac{\\sqrt{3}}{2}\\log_{e}\\left(\\dfrac{2\\sqrt{3}}{e}\\right)$",
            "$\\dfrac{\\pi}{12} + \\dfrac{\\sqrt{3}}{2}\\log_{e}\\left(\\dfrac{2}{e\\sqrt{3}}\\right)$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    101: {
        "format": "mcq",
        "body": "If $x = x(y)$ is the solution of the differential equation $y\\dfrac{dx}{dy} = 2x + y^{3}(y + 1)e^{y}$, $x(1) = 0$; then $x(e)$ is equal to",
        "options": [
            "$e^{e}(e^{3} - 1)$",
            "$e^{3}(e^{e} - 1)$",
            "$e^{e} - 1$",
            "$e^{e}(e^{2} - 1)$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    109: {
        "format": "mcq",
        "body": "Let $y(x)$ be the solution of the differential equation $2x^{2}\\,dy + (e^{y} - 2x)\\,dx = 0$, $x > 0$. If $y(e) = 1$, then $y(1)$ is equal to",
        "options": ["$\\log_{e}(2e)$", "$\\log_{e} 2$", "$2$", "$0$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    120: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation $e^{y}\\left(\\dfrac{dy}{dx} - 1\\right) = e^{x}$ such that $y(0) = 0$, then $y(1)$ is equal to",
        "options": ["$1 + \\log_{e} 2$", "$2 + \\log_{e} 2$", "$2e$", "$\\log_{e} 2$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    128: {
        "format": "mcq",
        "body": "If a curve passes through the point $(1, -2)$ and has slope of the tangent at any point $(x, y)$ on it as $\\dfrac{x^{2} - 2y}{x}$, then the curve also passes through which of the following points",
        "options": ["$(\\sqrt{3}, 0)$", "$(-1, 2)$", "$(-\\sqrt{2}, 1)$", "$(3, 0)$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
