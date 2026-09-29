#!/usr/bin/env python3
"""DE ch21 batch 10: Q191,192,193,194,197."""
from ch21_push import push_repairs

REPAIRS = {
    191: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution curve of the differential equation $\\sin(2x^{2})\\log_{e}(\\tan x^{2})\\,dy + (4xy - 4\\sqrt{2} x\\sin(x^{2} - \\pi/4))\\,dx = 0$, $0 < x < \\sqrt{\\pi/2}$, which passes through the point $(\\sqrt{\\pi/6}, 1)$. Then $|y(\\sqrt{\\pi/3})|$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "1",
    },
    192: {
        "format": "mcq",
        "body": "The slope of normal at any point $(x, y)$, $x > 0$, $y > 0$ on the curve $y = y(x)$ is given by $\\dfrac{x^{2}}{xy - x^{2}y^{2} - 1}$. If the curve passes through the point $(1, 1)$, then $e \\cdot y(e)$ is equal to",
        "options": [
            "$\\dfrac{1 - \\tan 1}{1 + \\tan 1}$",
            "$\\tan 1$",
            "$1$",
            "$\\dfrac{1 + \\tan 1}{1 - \\tan 1}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    193: {
        "format": "mcq",
        "body": "Let $x = x(y)$ be the solution of the differential equation $2y e^{x/y^{2}}\\,dx + (y^{2} - 4x e^{x/y^{2}})\\,dy = 0$ such that $x(1) = 0$. Then $x(e)$ is equal to",
        "options": [
            "$e\\log_{e} 2$",
            "$-e\\log_{e} 2$",
            "$e^{2}\\log_{e} 2$",
            "$-e^{2}\\log_{e} 2$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    194: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\left((x + 2)e^{(y+1)/(x+2)} + (y + 1)\\right)dx = (x + 2)\\,dy$, $y(1) = 1$. If the domain of $y = y(x)$ is an open interval $(\\alpha, \\beta)$, then $|\\alpha + \\beta|$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    197: {
        "format": "mcq",
        "body": "Let $f(x)$ be a differentiable function defined on $[0, 2]$ such that $f'(x) = f'(2 - x)$ for all $x \\in (0, 2)$, $f(0) = 1$ and $f(2) = e^{2}$. Then the value of $\\int_{0}^{2} f(x)\\,dx$ is",
        "options": ["$2(1 + e^{2})$", "$1 + e^{2}$", "$1 - e^{2}$", "$2(1 - e^{2})$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
