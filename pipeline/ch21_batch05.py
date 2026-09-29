#!/usr/bin/env python3
"""DE ch21 batch 5: Q71,73,76,86,87,88."""
from ch21_push import push_repairs

REPAIRS = {
    71: {
        "format": "mcq",
        "body": "If $x = f(y)$ is the solution of the differential equation $(1 + y^{2}) + \\left(x - 2e^{\\tan^{-1} y}\\right)\\dfrac{dy}{dx} = 0$, $y \\in (-\\pi/2, \\pi/2)$ with $f(0) = 1$, then $f(1/\\sqrt{3})$ is equal to",
        "options": ["$e^{\\pi/12}$", "$e^{\\pi/4}$", "$e^{\\pi/3}$", "$e^{\\pi/6}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    73: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\left(xy - 5x^{2}\\sqrt{1 + x^{2}}\\right)dx + (1 + x^{2})\\,dy = 0$, $y(0) = 0$. Then $y(\\sqrt{3})$ is equal to",
        "options": ["$\\sqrt{\\dfrac{15}{2}}$", "$\\dfrac{5\\sqrt{3}}{2}$", "$2\\sqrt{2}$", "$\\sqrt{\\dfrac{14}{3}}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    76: {
        "format": "numerical",
        "body": "If $y = y(x)$ is the solution of the differential equation $\\sqrt{4 - x^{2}}\\,\\dfrac{dy}{dx} = \\left(\\left(\\sin^{-1}\\left(\\dfrac{x}{2}\\right)\\right)^{2} - y\\right)\\sin^{-1}\\left(\\dfrac{x}{2}\\right)$, $-2 \\le x \\le 2$, $y(2) = \\dfrac{\\pi^{2} - 8}{4}$, then $y^{2}(0)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    86: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be a solution of the differential equation $(x\\cos x)\\,dy + (xy\\sin x + y\\cos x - 1)\\,dx = 0$, $0 < x < \\pi/2$. If $(\\pi/3) y(\\pi/3) = \\sqrt{3}$, then $\\left|(\\pi/6) y''(\\pi/6) + 2y'(\\pi/6)\\right|$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    87: {
        "format": "mcq",
        "body": "If the solution curve $f(x, y) = 0$ of the differential equation $(1 + \\log_{e} x)\\dfrac{dx}{dy} - x\\log_{e} x = e^{y}$, $x > 0$, passes through the points $(1, 0)$ and $(a, 2)$, then $a^{a}$ is equal to",
        "options": ["$e^{2e^{2}}$", "$e^{e^{2}}$", "$e^{\\sqrt{2}e^{2}}$", "$e^{2e\\sqrt{2}}$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    88: {
        "format": "numerical",
        "body": "If the solution curve of the differential equation $(y - 2\\log_{e} x)\\,dx + (x\\log_{e} x^{2})\\,dy = 0$, $x > 1$ passes through the points $(e, 4/3)$ and $(e^{4}, \\alpha)$, then $\\alpha$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
