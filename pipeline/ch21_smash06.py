#!/usr/bin/env python3
"""DE ch21 leftover smash: Q59,60,61,65,68,72."""
from ch21_push import push_repairs

REPAIRS = {
    59: {
        "format": "mcq",
        "body": "The solution curve of the differential equation $y\\dfrac{dx}{dy} = x(\\log_{e} x - \\log_{e} y + 1)$, $x > 0$, $y > 0$ passing through the point $(e, 1)$ is",
        "options": [
            "$\\left|\\log_{e}\\dfrac{y}{x}\\right| = x$",
            "$\\left|\\log_{e}\\dfrac{y}{x}\\right| = y^{2}$",
            "$\\left|\\log_{e}\\dfrac{x}{y}\\right| = y$",
            "$2\\left|\\log_{e}\\dfrac{x}{y}\\right| = y + 1$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    60: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(x^{2} - 3y^{2})\\,dx + 3xy\\,dy = 0$, $y(1) = 1$. Then $6y^{2}(e)$ is equal to",
        "options": ["$3e^{2}$", "$e^{2}$", "$2e^{2}$", "$\\dfrac{3e^{2}}{2}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    61: {
        "format": "mcq",
        "body": "The solution of the differential equation $\\dfrac{dy}{dx} = -\\left(\\dfrac{x^{2} + 3y^{2}}{3x^{2} + y^{2}}\\right)$, $y(1) = 0$ is",
        "options": [
            "$\\log_{e}|x + y| - \\dfrac{xy}{(x + y)^{2}} = 0$",
            "$\\log_{e}|x + y| + \\dfrac{xy}{(x + y)^{2}} = 0$",
            "$\\log_{e}|x + y| + \\dfrac{2xy}{(x + y)^{2}} = 0$",
            "$\\log_{e}|x + y| - \\dfrac{2xy}{(x + y)^{2}} = 0$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    65: {
        "format": "mcq",
        "body": "Let the solution curve of the differential equation $x\\dfrac{dy}{dx} - y = \\sqrt{y^{2} + 16x^{2}}$, $y(1) = 3$ be $y = y(x)$. Then $y(2)$ is equal to",
        "options": ["$15$", "$11$", "$14$", "$17$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    68: {
        "format": "mcq",
        "body": "If a curve $y = y(x)$ passes through the point $\\left(1, \\dfrac{\\pi}{2}\\right)$ and satisfies the differential equation $\\left(7x^{4}\\cot y - e^{x}\\operatorname{cosec} y\\right)\\dfrac{dx}{dy} = x^{5}$, $x \\ge 1$, then at $x = 2$, the value of $\\cos y$ is",
        "options": [
            "$\\dfrac{2e^{2} - e}{64}$",
            "$\\dfrac{2e^{2} + e}{64}$",
            "$\\dfrac{2e^{2} - e}{128}$",
            "$\\dfrac{2e^{2} + e}{128}$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    72: {
        "format": "mcq",
        "body": "Let a curve $y = f(x)$ pass through the points $(0, 5)$ and $(\\log_{e} 2, k)$. If the curve satisfies the differential equation $2(3 + y)e^{2x}\\,dx - (7 + e^{2x})\\,dy = 0$, then $k$ is equal to",
        "options": ["$4$", "$32$", "$8$", "$16$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
