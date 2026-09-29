#!/usr/bin/env python3
"""DE ch21 leftover smash: Q184,188."""
from ch21_push import push_repairs

REPAIRS = {
    184: {
        "format": "mcq",
        "body": "If the curve $y = y(x)$ is the solution of the differential equation $2(x^{2} + x^{5/4})\\,dy - y(x + x^{1/4})\\,dx = 2x^{9/4}\\,dx$, $x > 0$ which passes through the point $\\left(1, 1 - \\dfrac{4}{3}\\log_{e} 2\\right)$, then the value of $y(16)$ is equal to",
        "options": [
            "$4\\left(\\dfrac{31}{3} + \\dfrac{8}{3}\\log_{e} 3\\right)$",
            "$\\left(\\dfrac{31}{3} + \\dfrac{8}{3}\\log_{e} 3\\right)$",
            "$4\\left(\\dfrac{31}{3} - \\dfrac{8}{3}\\log_{e} 3\\right)$",
            "$\\left(\\dfrac{31}{3} - \\dfrac{8}{3}\\log_{e} 3\\right)$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    188: {
        "format": "mcq",
        "body": "If $y(x)$ is the solution of the differential equation $\\dfrac{dy}{dx} + \\left(\\dfrac{2x + 1}{x}\\right)y = e^{-2x}$, $x > 0$, where $y(1) = \\dfrac{1}{2}e^{-2}$, then which of the following is true",
        "options": [
            "$y(\\log_{e} 2) = \\log_{e} 4$",
            "$y(\\log_{e} 2) = \\dfrac{\\log_{e} 2}{4}$",
            "$y(x)$ is decreasing in $\\left(\\dfrac{1}{2}, 1\\right)$",
            "$y(x)$ is decreasing in $(0, 1)$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
