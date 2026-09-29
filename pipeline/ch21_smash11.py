#!/usr/bin/env python3
"""DE ch21 leftover smash: Q169,170,173,174,177,179."""
from ch21_push import push_repairs

REPAIRS = {
    169: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} + \\dfrac{2x}{(1 + x^{2})^{2}} y = x e^{1/(1 + x^{2})}$; $y(0) = 0$. Then the area enclosed by the curve $f(x) = y(x) e^{-1/(1 + x^{2})}$ and the line $y - x = 4$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "18",
    },
    170: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(2x\\log_{e} x)\\dfrac{dy}{dx} + 2y = \\dfrac{3}{x}\\log_{e} x$, $x > 0$ and $y(e^{-1}) = 0$. Then, $y(e)$ is equal to",
        "options": [
            "$-\\dfrac{3}{e}$",
            "$-\\dfrac{3}{2e}$",
            "$-\\dfrac{2}{3e}$",
            "$-\\dfrac{2}{e}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    173: {
        "format": "numerical",
        "body": "Let the solution curve $x = x(y)$, $0 < y < \\dfrac{\\pi}{2}$, of the differential equation $(\\log_{e}(\\cos y))^{2}\\cos y\\,dx - (1 + 3x\\log_{e}(\\cos y))\\sin y\\,dy = 0$ satisfy $x\\left(\\dfrac{\\pi}{3}\\right) = \\dfrac{1}{2\\log_{e} 2}$. If $x\\left(\\dfrac{\\pi}{6}\\right) = \\dfrac{1}{\\log_{e} m - \\log_{e} n}$, where $m$ and $n$ are coprime, then $mn$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "12",
    },
    174: {
        "format": "mcq",
        "body": "Let $x = x(y)$ be the solution of the differential equation $2(y + 2)\\log_{e}(y + 2)\\,dx + (x + 4 - 2\\log_{e}(y + 2))\\,dy = 0$, $y > -1$ with $x(e^{4} - 2) = 1$. Then $x(e^{9} - 2)$ is equal to",
        "options": ["$3$", "$\\dfrac{4}{9}$", "$\\dfrac{32}{9}$", "$\\dfrac{10}{3}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    177: {
        "format": "mcq",
        "body": "Let $\\alpha x = \\exp(x^{\\beta} y^{\\gamma})$ be the solution of the differential equation $2x^{2} y\\,dy - (1 - xy^{2})\\,dx = 0$, $x > 0$, $y(2) = \\sqrt{\\log_{e} 2}$. Then $\\alpha + \\beta - \\gamma$ is equal to",
        "options": ["$1$", "$-1$", "$0$", "$3$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    179: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(1 - x^{2})\\,dy = \\left(xy + (x^{3} + 2)\\sqrt{1 - x^{2}}\\right)dx$, $-1 < x < 1$ and $y(0) = 0$. If $\\int_{-1/2}^{1/2} \\sqrt{1 - x^{2}}\\, y(x)\\,dx = k$ then $k^{-1}$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "320",
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
