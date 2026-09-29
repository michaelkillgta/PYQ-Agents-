#!/usr/bin/env python3
"""DE ch21 leftover smash: Q74,78,79,84,93,94."""
from ch21_push import push_repairs

REPAIRS = {
    74: {
        "format": "numerical",
        "body": "Let $f$ be a differentiable function such that $2(x + 2)^{2} f(x) - 3(x + 2)^{2} = 10\\int_{0}^{x}(t + 2)f(t)\\,dt$, $x \\ge 0$. Then $f(2)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "19",
    },
    78: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution curve of the differential equation $\\sec y\\dfrac{dy}{dx} + 2x\\sin y = x^{3}\\cos y$, $y(1) = 0$. Then $y(\\sqrt{3})$ is equal to",
        "options": ["$\\dfrac{\\pi}{3}$", "$\\dfrac{\\pi}{6}$", "$\\dfrac{\\pi}{12}$", "$\\dfrac{\\pi}{4}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    79: {
        "format": "numerical",
        "body": "For a differentiable function $f : \\mathbb{R} \\to \\mathbb{R}$, suppose $f'(x) = 3f(x) + \\alpha$, where $\\alpha \\in \\mathbb{R}$, $f(0) = 1$ and $\\displaystyle\\lim_{x \\to -\\infty} f(x) = 7$. Then $9f(-\\log_{e} 3)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "61",
    },
    84: {
        "format": "mcq",
        "body": "Let $\\alpha$ be a non-zero real number. Suppose $f : R \\to R$ is a differentiable function such that $f(0) = 1$ and $\\displaystyle\\lim_{x \\to -\\infty} f(x) = 1$. If $f'(x) = \\alpha f(x) + 3$, for all $x \\in R$, then $f(-\\log_{e} 2)$ is equal to",
        "options": ["$1$", "$5$", "$9$", "$7$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    93: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution curve of the differential equation $\\dfrac{dy}{dx} = \\dfrac{y}{x}\\left(1 + x^{2}(1 + \\log_{e} x)\\right)$, $x > 0$, $y(1) = 3$. Then $\\dfrac{y^{2}(x)}{9}$ is equal to",
        "options": [
            "$\\dfrac{x^{2}}{5 - 2x^{3}(2 + \\log_{e} x^{3})}$",
            "$\\dfrac{x^{2}}{2x^{3}(2 + \\log_{e} x^{3}) - 3}$",
            "$\\dfrac{x^{2}}{3x^{3}(1 + \\log_{e} x^{2}) - 2}$",
            "$\\dfrac{x^{2}}{7 - 3x^{3}(2 + \\log_{e} x^{2})}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    94: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $x\\log_{e} x\\dfrac{dy}{dx} + y = x^{2}\\log_{e} x$, $(x > 1)$. If $y(2) = 2$, then $y(e)$ is equal to",
        "options": [
            "$\\dfrac{4 + e^{2}}{4}$",
            "$\\dfrac{1 + e^{2}}{4}$",
            "$\\dfrac{2 + e^{2}}{2}$",
            "$\\dfrac{1 + e^{2}}{2}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
