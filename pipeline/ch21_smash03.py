#!/usr/bin/env python3
"""DE ch21 leftover smash: Q1,5,6,8,16,21."""
from ch21_push import push_repairs

REPAIRS = {
    1: {
        "format": "numerical",
        "body": "The difference between degree and order of a differential equation that represents the family of curves given by $y^{2} = a\\left(x + \\dfrac{\\sqrt{a}}{2}\\right)$, $a > 0$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    5: {
        "format": "mcq",
        "body": "Let $y = y_{1}(x)$ and $y = y_{2}(x)$ be the solution curves of the differential equation $\\dfrac{dy}{dx} = y + 7$ with initial conditions $y_{1}(0) = 0$ and $y_{2}(0) = 1$ respectively. Then the curves $y = y_{1}(x)$ and $y = y_{2}(x)$ intersect at",
        "options": [
            "no point",
            "two points",
            "one point",
            "infinite number of points",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    6: {
        "format": "mcq",
        "body": "Let $y = f(x)$ be the solution of the differential equation $y(x + 1)\\,dx - x^{2}\\,dy = 0$, $y(1) = e$. Then $\\displaystyle\\lim_{x \\to 0^{+}} f(x)$ is equal to",
        "options": ["$0$", "$\\dfrac{1}{e}$", "$e^{2}$", "$\\dfrac{1}{e^{2}}$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    8: {
        "format": "mcq",
        "body": "Which of the following is true for $y(x)$ that satisfies the differential equation $\\dfrac{dy}{dx} = xy - 1 + x - y$; $y(0) = 0$",
        "options": [
            "$y(1) = e^{-1/2} - 1$",
            "$y(1) = e^{1/2} - e^{-1/2}$",
            "$y(1) = 1$",
            "$y(1) = e^{1/2} - 1$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    16: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $x^{3}\\,dy + (xy - 1)\\,dx = 0$, $x > 0$, $y\\left(\\dfrac{1}{2}\\right) = 3 - e$. Then $y(1)$ is equal to",
        "options": ["$1$", "$e$", "$2 - e$", "$3$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    21: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution curve of the differential equation $x^{2}\\,dy + \\left(y - \\dfrac{1}{x}\\right)dx = 0$; $x > 0$ and $y(1) = 1$, then $y\\left(\\dfrac{1}{2}\\right)$ is equal to",
        "options": [
            "$3 + e$",
            "$3 - e$",
            "$\\dfrac{3}{2} - \\dfrac{1}{\\sqrt{e}}$",
            "$3 + \\dfrac{1}{\\sqrt{e}}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
