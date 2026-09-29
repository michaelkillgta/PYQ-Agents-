#!/usr/bin/env python3
"""DE ch21 leftover smash: Q99,102,104,107,113,118."""
from ch21_push import push_repairs

REPAIRS = {
    99: {
        "format": "mcq",
        "body": "Let the solution curve $y = y(x)$ of the differential equation $(1 + e^{2x})\\left(\\dfrac{dy}{dx} + y\\right) = 1$ pass through the point $\\left(0, \\dfrac{\\pi}{2}\\right)$. Then $\\displaystyle\\lim_{x \\to \\infty} e^{x} y(x)$ is equal to",
        "options": ["$\\dfrac{\\pi}{4}$", "$\\dfrac{3\\pi}{4}$", "$\\dfrac{\\pi}{2}$", "$\\dfrac{3\\pi}{2}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    102: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation $2x^{2}\\dfrac{dy}{dx} - 2xy + 3y^{2} = 0$ such that $y(e) = \\dfrac{e}{3}$, then $y(1)$ is equal to",
        "options": ["$\\dfrac{1}{3}$", "$\\dfrac{2}{3}$", "$\\dfrac{3}{2}$", "$3$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    104: {
        "format": "mcq",
        "body": "If $\\dfrac{dy}{dx} + e^{x}(x^{2} - 2)y = (x^{2} - 2x)(x^{2} - 2)e^{2x}$ and $y(0) = 0$, then the value of $y(2)$ is",
        "options": ["$-1$", "$1$", "$0$", "$e$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    107: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $x(1 - x^{2})\\dfrac{dy}{dx} + (3x^{2}y - y - 4x^{3}) = 0$, $x > 1$ with $y(2) = -2$. Then $y(3)$ is equal to",
        "options": ["$-18$", "$-12$", "$-6$", "$-3$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    113: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\operatorname{cosec}^{2} x\\,dy + 2\\,dx = (1 + y\\cos 2x)\\operatorname{cosec}^{2} x\\,dx$, with $y\\left(\\dfrac{\\pi}{4}\\right) = 0$. Then, the value of $(y(0) + 1)^{2}$ is equal to",
        "options": ["$e^{1/2}$", "$e^{-1/2}$", "$e^{-1}$", "$e$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    118: {
        "format": "mcq",
        "body": "If a curve $y = f(x)$, passing through the point $(1, 2)$, is the solution of the differential equation $2x^{2}\\,dy = (2xy + y^{2})\\,dx$, then $f\\left(\\dfrac{1}{2}\\right)$ is equal to",
        "options": [
            "$\\dfrac{1}{1 + \\log_{e} 2}$",
            "$\\dfrac{1}{1 - \\log_{e} 2}$",
            "$1 + \\log_{e} 2$",
            "$\\dfrac{-1}{1 + \\log_{e} 2}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
