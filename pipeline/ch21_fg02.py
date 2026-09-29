#!/usr/bin/env python3
"""DE ch21 fill-gate batch B: Q43,44,46,53,54,56."""
from ch21_push import push_repairs

REPAIRS = {
    43: {
        "format": "mcq",
        "body": "If $\\dfrac{dy}{dx} = \\dfrac{2^{x+y} - 2^{x}}{2^{y}}$, $y(0) = 1$, then $y(1)$ is equal to",
        "options": [
            "$\\log_{2}(1 + e^{2})$",
            "$\\log_{2}(2e)$",
            "$\\log_{2}(2 + e)$",
            "$\\log_{2}(1 + e)$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    44: {
        "format": "mcq",
        "body": "If $\\dfrac{dy}{dx} = \\dfrac{2^{x} y + 2^{y} \\cdot 2^{x}}{2^{x} + 2^{x+y}\\log_{e} 2}$, $y(0) = 0$, then for $y = 1$, the value of $x$ lies in the interval",
        "options": ["$(1, 2)$", "$(1/2, 1]$", "$(2, 3)$", "$(0, 1/2]$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    46: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} = 1 + x e^{y-x}$, $-\\sqrt{2} < x < \\sqrt{2}$, $y(0) = 0$, then the minimum value of $y(x)$, $x \\in (-\\sqrt{2}, \\sqrt{2})$ is equal to",
        "options": [
            "$(2 - \\sqrt{3}) - \\log_{e} 2$",
            "$(2 + \\sqrt{3}) + \\log_{e} 2$",
            "$(1 + \\sqrt{3}) - \\log_{e}(\\sqrt{3} - 1)$",
            "$(1 - \\sqrt{3}) - \\log_{e}(\\sqrt{3} - 1)$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    53: {
        "format": "mcq",
        "body": "If $f'(x) = \\tan^{-1}(\\sec x + \\tan x)$, $-\\pi/2 < x < \\pi/2$ and $f(0) = 0$, then $f(1)$ is equal to",
        "options": [
            "$\\dfrac{\\pi + 1}{4}$",
            "$\\dfrac{1}{4}$",
            "$\\dfrac{\\pi - 1}{4}$",
            "$\\dfrac{\\pi + 2}{4}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    54: {
        "format": "mcq",
        "body": "The solution of the differential equation $\\dfrac{dy}{dx} = (x - y)^{2}$, when $y(1) = 1$, is",
        "options": [
            "$\\log_{e}\\left|\\dfrac{2 - x}{2 - y}\\right| = x - y$",
            "$-\\log_{e}\\left|\\dfrac{1 - x + y}{1 + x - y}\\right| = 2(x - 1)$",
            "$-\\log_{e}\\left|\\dfrac{1 + x - y}{1 - x + y}\\right| = x + y - 2$",
            "$\\log_{e}\\left|\\dfrac{2 - y}{2 - x}\\right| = 2(y - 1)$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    56: {
        "format": "mcq",
        "body": "The solution curve of the differential equation $2y\\dfrac{dy}{dx} + 3 = 5\\dfrac{dy}{dx}$, passing through the point $(0, 1)$ is a conic, whose vertex lies on which of the following lines",
        "options": ["$2x + 3y = 9$", "$2x + 3y = -9$", "$2x + 3y = -6$", "$2x + 3y = 6$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
