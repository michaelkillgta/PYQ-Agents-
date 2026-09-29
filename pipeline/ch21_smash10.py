#!/usr/bin/env python3
"""DE ch21 leftover smash: Q148,155,161,163,165,168."""
from ch21_push import push_repairs

REPAIRS = {
    148: {
        "format": "mcq",
        "body": "Let $x = x(t)$ and $y = y(t)$ be solutions of the differential equations $\\dfrac{dx}{dt} + ax = 0$ and $\\dfrac{dy}{dt} + by = 0$ respectively, $a, b \\in \\mathbb{R}$. Given that $x(0) = 2$; $y(0) = 1$ and $3y(1) = 2x(1)$, the value of $t$, for which $x(t) = y(t)$, is",
        "options": [
            "$\\log_{2/3} 2$",
            "$\\log_{4} 3$",
            "$\\log_{3} 4$",
            "$\\log_{4/3} 2$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    155: {
        "format": "numerical",
        "body": "If the solution curve, of the differential equation $\\dfrac{dy}{dx} = \\dfrac{x + y - 2}{x - y}$ passing through the point $(2, 1)$ is $\\tan^{-1}\\left(\\dfrac{y - 1}{x - 1}\\right) - \\dfrac{1}{\\beta}\\log_{e}\\left(\\alpha + \\left(\\dfrac{y - 1}{x - 1}\\right)^{2}\\right) = \\log_{e}|x - 1|$, then $5\\beta + \\alpha$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "11",
    },
    161: {
        "format": "mcq",
        "body": "Let $f : [1, \\infty) \\to [2, \\infty)$ be a differentiable function. If $10\\int_{1}^{x} f(t)\\,dt = 5x f(x) - x^{5} - 9$ for all $x \\ge 1$, then the value of $f(3)$ is",
        "options": ["$18$", "$32$", "$22$", "$26$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    163: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution curve of the differential equation $x(x^{2} + e^{x})\\,dy + (e^{x}(x - 2)y - x^{3})\\,dx = 0$, $x > 0$ passing through the point $(1, 0)$. Then $y(2)$ is equal to",
        "options": [
            "$\\dfrac{4}{4 - e^{2}}$",
            "$\\dfrac{2}{2 + e^{2}}$",
            "$\\dfrac{2}{2 - e^{2}}$",
            "$\\dfrac{4}{4 + e^{2}}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    165: {
        "format": "numerical",
        "body": "Let $y = f(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} + \\dfrac{xy}{x^{2} - 1} = \\dfrac{x^{6} + 4x}{\\sqrt{1 - x^{2}}}$, $-1 < x < 1$ such that $f(0) = 0$. If $6\\int_{-1/2}^{1/2} f(x)\\,dx = 2\\pi - \\alpha$ then $\\alpha^{2}$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "27",
    },
    168: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(x^{2} + 4)^{2}\\,dy + (2x^{3}y + 8xy - 2)\\,dx = 0$. If $y(0) = 0$, then $y(2)$ is equal to",
        "options": ["$\\dfrac{\\pi}{32}$", "$2\\pi$", "$\\dfrac{\\pi}{8}$", "$\\dfrac{\\pi}{16}$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
