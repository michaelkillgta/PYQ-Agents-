#!/usr/bin/env python3
"""DE ch21 leftover smash: Q47,51,52,55,57,58."""
from ch21_push import push_repairs

REPAIRS = {
    47: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be solution of the differential equation $\\log_{e}\\left(\\dfrac{dy}{dx}\\right) = 3x + 4y$, with $y(0) = 0$. If $y\\left(-\\dfrac{2}{3}\\log_{e} 2\\right) = \\alpha\\log_{e} 2$, then the value of $\\alpha$ is equal to",
        "options": ["$-\\dfrac{1}{4}$", "$\\dfrac{1}{4}$", "$2$", "$-\\dfrac{1}{2}$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    51: {
        "format": "mcq",
        "body": "The solution of the differential equation $\\dfrac{dy}{dx} - \\dfrac{y + 3x}{\\log_{e}(y + 3x)} + 3 = 0$ is (where $C$ is a constant of integration)",
        "options": [
            "$x - \\dfrac{1}{2}(\\log_{e}(y + 3x))^{2} = C$",
            "$x - \\log_{e}(y + 3x) = C$",
            "$y + 3x - \\dfrac{1}{2}(\\log_{e} x)^{2} = C$",
            "$x - 2\\log_{e}(y + 3x) = C$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    52: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation $\\dfrac{5 + e^{x}}{2 + y} \\cdot \\dfrac{dy}{dx} + e^{x} = 0$ satisfying $y(0) = 1$ then value of $y(\\log_{e} 13)$ is",
        "options": ["$1$", "$-1$", "$0$", "$2$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    55: {
        "format": "mcq",
        "body": "Let $x = x(y)$ be the solution of the differential equation $y = \\left(x - y\\dfrac{dx}{dy}\\right)\\sin\\left(\\dfrac{x}{y}\\right)$, $y > 0$ and $x(1) = \\dfrac{\\pi}{2}$. Then $\\cos(x(2))$ is equal to",
        "options": [
            "$1 - 2(\\log_{e} 2)^{2}$",
            "$1 - 2(\\log_{e} 2)$",
            "$2(\\log_{e} 2) - 1$",
            "$2(\\log_{e} 2)^{2} - 1$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    57: {
        "format": "numerical",
        "body": "If the solution of the differential equation $(2x + 3y - 2)\\,dx + (4x + 6y - 7)\\,dy = 0$, $y(0) = 3$, is $\\alpha x + \\beta y + 3\\log_{e}|2x + 3y - \\gamma| = 6$, then $\\alpha + 2\\beta + 3\\gamma$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "29",
    },
    58: {
        "format": "mcq",
        "body": "If $\\sin\\left(\\dfrac{y}{x}\\right) = \\log_{e}|x| + \\dfrac{\\alpha}{2}$ is the solution of the differential equation $x\\cos\\left(\\dfrac{y}{x}\\right)\\dfrac{dy}{dx} = y\\cos\\left(\\dfrac{y}{x}\\right) + x$ and $y(1) = \\dfrac{\\pi}{3}$, then $\\alpha^{2}$ is equal to",
        "options": ["$3$", "$12$", "$4$", "$9$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
