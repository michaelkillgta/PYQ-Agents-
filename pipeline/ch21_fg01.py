#!/usr/bin/env python3
"""DE ch21 fill-gate batch A: Q25,31,36,39,41,42."""
from ch21_push import push_repairs

REPAIRS = {
    25: {
        "format": "mcq",
        "body": "The solution of the differential equation $x\\dfrac{dy}{dx} + 2y = x^{2}$, $(x \\ne 0)$ with $y(1) = 1$, is",
        "options": [
            "$y = \\dfrac{x^{3}}{5} + \\dfrac{1}{5x^{2}}$",
            "$y = \\dfrac{3}{4}x^{2} + \\dfrac{1}{4x^{2}}$",
            "$y = \\dfrac{x^{2}}{4} + \\dfrac{3}{4x^{2}}$",
            "$y = \\dfrac{4}{5}x^{3} + \\dfrac{1}{5x^{2}}$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    31: {
        "format": "mcq",
        "body": "The rate of growth of bacteria in a culture is proportional to the number of bacteria present and the bacteria count is $1000$ at initial time $t = 0$. The number of bacteria is increased by $20\\%$ in $2$ hours. If the population of bacteria is $2000$ after $\\dfrac{k}{\\log_{e}(6/5)}$ hours, then $\\left(\\dfrac{k}{\\log_{e} 2}\\right)^{2}$ is equal to",
        "options": ["$8$", "$4$", "$16$", "$2$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    36: {
        "format": "mcq",
        "body": "The solution of the differential equation $(x^{2} + y^{2})\\,dx - 5xy\\,dy = 0$, $y(1) = 0$, is",
        "options": [
            "$|x^{2} - 2y^{2}|^{6} = x$",
            "$|x^{2} - 4y^{2}|^{6} = x$",
            "$|x^{2} - 4y^{2}|^{5} = x^{2}$",
            "$|x^{2} - 2y^{2}|^{5} = x^{2}$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    39: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\sec x\\,dy + \\{2(1 - x)\\tan x + x(2 - x)\\}\\,dx = 0$ such that $y(0) = 2$. Then $y(2)$ is equal to",
        "options": ["$2$", "$2\\{1 - \\sin 2\\}$", "$2\\{\\sin 2 + 1\\}$", "$1$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    41: {
        "format": "mcq",
        "body": "If the solution curve of the differential equation $\\dfrac{dy}{dx} = \\dfrac{x + y - 2}{x - y}$ passes through the point $(2, 1)$ and $(k + 1, 2)$, $k > 0$, then which of the following is true",
        "options": [
            "$2\\tan^{-1}(1/k) = \\log_{e}(k^{2} + 1)$",
            "$\\tan^{-1}(1/k) = \\log_{e}(k^{2} + 1)$",
            "$2\\tan^{-1}(1/(k + 1)) = \\log_{e}(k^{2} + 2k + 2)$",
            "$2\\tan^{-1}(1/k) = \\log_{e}\\left(\\dfrac{k^{2} + 1}{k^{2}}\\right)$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    42: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation $(1 + e^{2x})\\dfrac{dy}{dx} + 2(1 + y^{2})e^{x} = 0$ and $y(0) = 0$, then $6\\left(y'(0) + \\left(y(\\log_{e}\\sqrt{3})\\right)^{2}\\right)$ is equal to",
        "options": ["$2$", "$-2$", "$-4$", "$-1$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
