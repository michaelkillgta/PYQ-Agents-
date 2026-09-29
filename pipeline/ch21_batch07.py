#!/usr/bin/env python3
"""DE ch21 batch 7: Q121,123,125,134,135,136."""
from ch21_push import push_repairs

REPAIRS = {
    121: {
        "format": "numerical",
        "body": "If for $x \\ge 0$, $y = y(x)$ is the solution of the differential equation $(x + 1)\\,dy = \\left((x + 1)^{2} + y - 3\\right)dx$, $y(2) = 0$ then $y(3)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    123: {
        "format": "mcq",
        "body": "If $\\cos x\\,\\dfrac{dy}{dx} - y\\sin x = 6x$, $(0 < x < \\pi/2)$ and $y(\\pi/3) = 0$, then $y(\\pi/6)$ is equal to",
        "options": [
            "$-\\dfrac{\\pi^{2}}{4\\sqrt{3}}$",
            "$\\dfrac{\\pi^{2}}{2\\sqrt{3}}$",
            "$-\\dfrac{\\pi^{2}}{2}$",
            "$-\\dfrac{\\pi^{2}}{2\\sqrt{3}}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    125: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} + y\\tan x = 2x + x^{2}\\tan x$, $x \\in (-\\pi/2, \\pi/2)$, such that $y(0) = 1$. Then which of the following is true",
        "options": [
            "$y'(\\pi/4) - y'(-\\pi/4) = \\pi - \\sqrt{2}$",
            "$y'(\\pi/4) + y'(-\\pi/4) = -\\sqrt{2}$",
            "$y(\\pi/4) - y(-\\pi/4) = \\sqrt{2}$",
            "$y'(\\pi/4) + y'(-\\pi/4) = \\dfrac{\\pi^{2}}{2} + 2$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    134: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $x\\,dy - y\\,dx = \\sqrt{x^{2} - y^{2}}\\,dx$, $x \\ge 1$, with $y(1) = 0$. If the area bounded by the line $x = 1$, $x = e^{\\pi}$, $y = 0$ and $y = y(x)$ is $\\alpha e^{2\\pi} + \\beta$, then the value of $10(\\alpha + \\beta)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    135: {
        "format": "numerical",
        "body": "If the curve $y = y(x)$ represented by the solution of the differential equation $(2xy^{2} - y)\\,dx + x\\,dy = 0$, passes through the intersection of the lines $2x - 3y = 1$ and $3x + 2y = 8$, then $|y(1)|$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "1",
    },
    136: {
        "format": "mcq",
        "body": "The general solution of the differential equation $(y^{2} - x^{3})\\,dx - xy\\,dy = 0$, $(x \\ne 0)$ is (where $c$ is a constant of integration)",
        "options": [
            "$y^{2} + 2x^{2} + cx^{3} = 0$",
            "$y^{2} - 2x^{2} + cx^{3} = 0$",
            "$y^{2} - 2x^{3} + cx^{2} = 0$",
            "$y^{2} + 2x^{3} + cx^{2} = 0$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
