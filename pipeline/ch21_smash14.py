#!/usr/bin/env python3
"""DE ch21 leftover smash: Q81,103,108,112,114,124."""
from ch21_push import push_repairs

REPAIRS = {
    81: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(1 - x^{2})\\,dy = \\left[xy + (x^{3} + 2)\\sqrt{3(1 - x^{2})}\\right]dx$, $-1 < x < 1$, $y(0) = 0$. If $y\\left(\\dfrac{1}{2}\\right) = \\dfrac{m}{n}$, $m$ and $n$ are coprime numbers, then $m + n$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "97",
    },
    103: {
        "format": "numerical",
        "body": "Let the solution curve $y = y(x)$ of the differential equation $(4 + x^{2})\\,dy - 2x(x^{2} + 3y + 4)\\,dx = 0$ pass through the origin. Then $y(2)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "12",
    },
    108: {
        "format": "numerical",
        "body": "Let $y = y(x)$, $x > 1$, be the solution of the differential equation $(x - 1)\\dfrac{dy}{dx} + 2xy = \\dfrac{1}{x - 1}$, with $y(2) = \\dfrac{1 + e^{4}}{2e^{4}}$. If $y(3) = \\dfrac{e^{\\alpha} + 1}{\\beta e^{\\alpha}}$, then the value of $\\alpha + \\beta$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "14",
    },
    112: {
        "format": "mcq",
        "body": "Let $y = y(x)$ satisfy the equation $\\dfrac{dy}{dx} = |A|$ for all $x > 0$, where $A = \\begin{bmatrix} y & \\sin x & 1 \\\\ 0 & 1 & 1 \\\\ 2 & 0 & \\dfrac{1}{x} \\end{bmatrix}$. If $y(\\pi) = \\pi + 2$, then the value of $y\\left(\\dfrac{\\pi}{2}\\right)$ is",
        "options": [
            "$\\dfrac{\\pi}{2} + \\dfrac{4}{\\pi}$",
            "$\\dfrac{\\pi}{2} - \\dfrac{1}{\\pi}$",
            "$\\dfrac{3\\pi}{2} - \\dfrac{1}{\\pi}$",
            "$\\dfrac{\\pi}{2} - \\dfrac{4}{\\pi}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    114: {
        "format": "mcq",
        "body": "If a curve $y = f(x)$ passes through the point $(1, 2)$ and satisfies $x\\dfrac{dy}{dx} + y = bx^{4}$, then for what value of $b$ is $\\int_{1}^{2} f(x)\\,dx = \\dfrac{62}{5}$",
        "options": ["$\\dfrac{31}{5}$", "$10$", "$5$", "$\\dfrac{62}{5}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    124: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation $\\dfrac{dy}{dx} = (\\tan x - y)\\sec^{2} x$, $x \\in \\left(-\\dfrac{\\pi}{2}, \\dfrac{\\pi}{2}\\right)$, such that $y(0) = 0$, then $y\\left(-\\dfrac{\\pi}{4}\\right)$ is equal to",
        "options": ["$\\dfrac{1}{e} - 2$", "$2 + \\dfrac{1}{e}$", "$e - 2$", "$\\dfrac{1}{2} - e$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
