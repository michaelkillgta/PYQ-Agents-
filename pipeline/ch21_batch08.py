#!/usr/bin/env python3
"""DE ch21 batch 8: Q143,150,151,158,166,167."""
from ch21_push import push_repairs

REPAIRS = {
    143: {
        "format": "numerical",
        "body": "Let a curve $y = f(x)$ pass through the point $(2, (\\log_{e} 2)^{2})$ and have slope $\\dfrac{2y}{x\\log_{e} x}$ for all positive real values of $x$. Then the value of $f(e)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "1",
    },
    150: {
        "format": "numerical",
        "body": "Let a curve $y = y(x)$ be given by the solution of the differential equation $\\cos\\left(\\dfrac{1}{2}\\cos^{-1}(e^{-x})\\right)dx = \\left(\\sqrt{e^{2x} - 1}\\right)dy$. If it intersects $y$-axis at $y = -1$, and the intersection point of the curve with $x$-axis is $(\\alpha, 0)$, then $e^{\\alpha}$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    151: {
        "format": "mcq",
        "body": "If $x^{3}\\,dy + xy\\,dx = x^{2}\\,dy + 2y\\,dx$; $y(2) = e$ and $x > 1$, then $y(4)$ is equal to",
        "options": ["$\\dfrac{\\sqrt{e}}{2}$", "$\\dfrac{1}{2} + \\sqrt{e}$", "$\\dfrac{3}{2}\\sqrt{e}$", "$\\dfrac{3}{2} + \\sqrt{e}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    158: {
        "format": "mcq",
        "body": "If $y\\dfrac{dy}{dx} = x\\left[\\dfrac{y^{2}}{x^{2}} + \\dfrac{\\phi(y^{2}/x^{2})}{\\phi'(y^{2}/x^{2})}\\right]$, $x > 0$, $\\phi > 0$, and $y(1) = -1$, then $\\phi(y^{2}/4)$ is equal to",
        "options": ["$2\\phi(1)$", "$\\phi(1)$", "$4\\phi(2)$", "$4\\phi(1)$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    166: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\cos x (\\log_{e}(\\cos x))^{2}\\,dy + (\\sin x - 3y\\sin x\\log_{e}(\\cos x))\\,dx = 0$, $x \\in (0, \\pi/2)$. If $y(\\pi/4) = \\dfrac{-1}{\\log_{e} 2}$, then $y(\\pi/6)$ is equal to",
        "options": [
            "$\\dfrac{1}{\\log_{e} 3 - \\log_{e} 4}$",
            "$\\dfrac{2}{\\log_{e} 3 - \\log_{e} 4}$",
            "$\\dfrac{1}{\\log_{e} 4 - \\log_{e} 3}$",
            "$-\\dfrac{1}{\\log_{e} 4}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    167: {
        "format": "mcq",
        "body": "If for the solution curve $y = f(x)$ of the differential equation $\\dfrac{dy}{dx} + (\\tan x)y = \\dfrac{2 + \\sec x}{(1 + 2\\sec x)^{2}}$, $x \\in (-\\pi/2, \\pi/2)$, $f(\\pi/3) = \\dfrac{\\sqrt{3}}{10}$, then $f(\\pi/4)$ is equal to",
        "options": [
            "$\\dfrac{\\sqrt{3} + 1}{10(4 + \\sqrt{3})}$",
            "$\\dfrac{5 - \\sqrt{3}}{2\\sqrt{2}}$",
            "$\\dfrac{9\\sqrt{3} + 3}{10(4 + \\sqrt{3})}$",
            "$\\dfrac{4 - \\sqrt{2}}{14}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
