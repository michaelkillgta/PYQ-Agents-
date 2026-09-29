#!/usr/bin/env python3
"""DE ch21 batch 6: Q89,90,92,95,97,116."""
from ch21_push import push_repairs

REPAIRS = {
    89: {
        "format": "mcq",
        "body": "Let $f$ be a differentiable function such that $x^{2} f(x) - x = 4\\int_{0}^{x} t f(t)\\,dt$, $f(1) = \\dfrac{2}{3}$. Then $18 f(3)$ is equal to",
        "options": ["$210$", "$160$", "$150$", "$180$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    90: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} + \\dfrac{5}{x(x^{5} + 1)} y = \\dfrac{(x^{5} + 1)^{2}}{x^{7}}$, $x > 0$. If $y(1) = 2$, then $y(2)$ is equal to",
        "options": [
            "$\\dfrac{637}{128}$",
            "$\\dfrac{679}{128}$",
            "$\\dfrac{693}{128}$",
            "$\\dfrac{697}{128}$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    92: {
        "format": "numerical",
        "body": "If $y = y(x)$ is the solution of the differential equation $\\dfrac{dy}{dx} + \\dfrac{4x}{x^{2} - 1} y = \\dfrac{x + 2}{(x^{2} - 1)^{5/2}}$, $x > 1$ such that $y(2) = \\dfrac{2}{9}\\log_{e}(2 + \\sqrt{3})$ and $y(\\sqrt{2}) = \\alpha\\log_{e}(\\sqrt{\\alpha} + \\beta) + \\beta - \\sqrt{\\gamma}$, $\\alpha, \\beta, \\gamma \\in \\mathbb{N}$, then $\\alpha\\beta\\gamma$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "6",
    },
    95: {
        "format": "numerical",
        "body": "Suppose $y = y(x)$ be the solution curve to the differential equation $\\dfrac{dy}{dx} - y = 2 - e^{-x}$ such that $\\lim_{x \\to \\infty} y(x)$ is finite. If $a$ and $b$ are respectively the $x$- and $y$-intercept of the tangent to the curve at $x = 0$, then the value of $a - 4b$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    97: {
        "format": "mcq",
        "body": "If $y = y(x)$, $x \\in (0, \\pi/2)$ be the solution curve of the differential equation $(\\sin^{2} 2x)\\dfrac{dy}{dx} + (8\\sin^{2} 2x + 2\\sin 4x)y = 2e^{-4x}(2\\sin 2x + \\cos 2x)$, with $y(\\pi/4) = e^{-\\pi}$, then $y(\\pi/6)$ is equal to",
        "options": [
            "$\\dfrac{2}{\\sqrt{3}} e^{-2\\pi/3}$",
            "$\\dfrac{2}{\\sqrt{3}} e^{2\\pi/3}$",
            "$\\dfrac{1}{\\sqrt{3}} e^{-2\\pi/3}$",
            "$\\dfrac{1}{\\sqrt{3}} e^{2\\pi/3}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    116: {
        "format": "numerical",
        "body": "If $y = y(x)$ is the solution of the equation $e^{\\sin y}\\cos y\\,\\dfrac{dy}{dx} + e^{\\sin y}\\cos x = \\cos x$, $y(0) = 0$; then $1 + y(\\pi/6) + \\dfrac{\\sqrt{3}}{2} y(\\pi/3) + \\dfrac{1}{\\sqrt{2}} y(\\pi/4)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "1",
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
