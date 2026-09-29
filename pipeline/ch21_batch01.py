#!/usr/bin/env python3
"""DE ch21 batch 1: Q2,3,4,7,10,11."""
from ch21_push import push_repairs

REPAIRS = {
    2: {
        "format": "mcq",
        "body": "The differential equation of the family of circles passing through the origin and having centre at the line $y = x$ is",
        "options": [
            "$(x^{2} - y^{2} + 2xy)\\,dx = (x^{2} - y^{2} - 2xy)\\,dy$",
            "$(x^{2} + y^{2} + 2xy)\\,dx = (x^{2} + y^{2} - 2xy)\\,dy$",
            "$(x^{2} + y^{2} - 2xy)\\,dx = (x^{2} + y^{2} + 2xy)\\,dy$",
            "$(x^{2} - y^{2} + 2xy)\\,dx = (x^{2} - y^{2} + 2xy)\\,dy$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    3: {
        "format": "mcq",
        "body": "The differential equation satisfied by the system of parabolas $y^{2} = 4a(x + a)$ is",
        "options": [
            "$y\\left(\\dfrac{dy}{dx}\\right)^{2} - 2x\\left(\\dfrac{dy}{dx}\\right) - y = 0$",
            "$y\\left(\\dfrac{dy}{dx}\\right)^{2} - 2x\\left(\\dfrac{dy}{dx}\\right) + y = 0$",
            "$y\\left(\\dfrac{dy}{dx}\\right)^{2} + 2x\\left(\\dfrac{dy}{dx}\\right) - y = 0$",
            "$y\\left(\\dfrac{dy}{dx}\\right) + 2x\\left(\\dfrac{dy}{dx}\\right) - y = 0$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    4: {
        "format": "mcq",
        "body": "The differential equation of the family of curves $x^{2} = 4b(y + b)$, $b \\in \\mathbb{R}$, is",
        "options": [
            "$x(y')^{2} = x + 2yy'$",
            "$x(y')^{2} = 2yy' - x$",
            "$xy'' = y'$",
            "$x(y')^{2} = x - 2yy'$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    7: {
        "format": "mcq",
        "body": "If $\\dfrac{dy}{dx} + \\dfrac{2^{x-y}(2^{y} - 1)}{2^{x} - 1} = 0$, $x, y > 0$, $y(1) = 1$, then $y(2)$ is equal to",
        "options": [
            "$2 + \\log_{2} 3$",
            "$2 + \\log_{2} 2$",
            "$2 - \\log_{2} 2$",
            "$2 - \\log_{2} 3$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    10: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be a solution of the differential equation $\\sqrt{1 - x^{2}}\\,\\dfrac{dy}{dx} + \\sqrt{1 - y^{2}} = 0$, $|x| < 1$. If $y\\left(\\dfrac{1}{2}\\right) = \\dfrac{\\sqrt{3}}{2}$, then $y\\left(\\dfrac{-1}{\\sqrt{2}}\\right)$ is equal to",
        "options": [
            "$\\dfrac{\\sqrt{3}}{2}$",
            "$-\\dfrac{1}{\\sqrt{2}}$",
            "$\\dfrac{1}{\\sqrt{2}}$",
            "$-\\dfrac{\\sqrt{3}}{2}$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    11: {
        "format": "mcq",
        "body": "The slope of tangent at any point $(x, y)$ on a curve $y = y(x)$ is $\\dfrac{x^{2} + y^{2}}{2xy}$, $x > 0$. If $y(2) = 0$, then a value of $y(8)$ is",
        "options": ["$-4\\sqrt{2}$", "$2\\sqrt{3}$", "$-2\\sqrt{3}$", "$4\\sqrt{3}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
