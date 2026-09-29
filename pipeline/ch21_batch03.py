#!/usr/bin/env python3
"""DE ch21 batch 3: Q35,37,38,40,48,49."""
from ch21_push import push_repairs

REPAIRS = {
    35: {
        "format": "numerical",
        "body": "If the solution $y(x)$ of the given differential equation $(e^{y} + 1)\\cos x\\,dx + e^{y}\\sin x\\,dy = 0$ passes through the point $\\left(\\dfrac{\\pi}{2}, 0\\right)$, then the value of $e^{y(\\pi/6)}$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    37: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution curve of the differential equation $(x^{2} - 4)\\,dy - (y^{2} - 3y)\\,dx = 0$, $x > 2$, $y(4) = \\dfrac{3}{2}$ and the slope of the curve is never zero, then the value of $y(10)$ equals",
        "options": [
            "$\\dfrac{3}{1 + (8)^{1/4}}$",
            "$\\dfrac{3}{1 + 2\\sqrt{2}}$",
            "$\\dfrac{3}{1 - 2\\sqrt{2}}$",
            "$\\dfrac{3}{1 - (8)^{1/4}}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    38: {
        "format": "numerical",
        "body": "If the solution curve $y = y(x)$ of the differential equation $(1 + y^{2})(1 + \\log_{e} x)\\,dx + x\\,dy = 0$, $x > 0$ passes through the point $(1, 1)$ and $y(e) = \\dfrac{\\alpha - \\tan(3/2)}{\\beta + \\tan(3/2)}$, then $\\alpha + 2\\beta$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    40: {
        "format": "mcq",
        "body": "The slope of the tangent to a curve $C : y = y(x)$ at any point $(x, y)$ on it is $\\dfrac{2e^{2x} - 6e^{-x} + 9}{2 + 9e^{-2x}}$. If $C$ passes through the points $\\left(0, \\dfrac{1}{2} + \\dfrac{\\pi}{2\\sqrt{2}}\\right)$ and $\\left(\\alpha, \\dfrac{1}{2}e^{2\\alpha}\\right)$, then $e^{\\alpha}$ is equal to",
        "options": [
            "$\\dfrac{3 + \\sqrt{2}}{3 - \\sqrt{2}}$",
            "$\\dfrac{3}{\\sqrt{2}}\\left(\\dfrac{3 + \\sqrt{2}}{3 - \\sqrt{2}}\\right)$",
            "$\\dfrac{1}{\\sqrt{2}}\\left(\\dfrac{\\sqrt{2} + 1}{\\sqrt{2} - 1}\\right)$",
            "$\\dfrac{\\sqrt{2} + 1}{\\sqrt{2} - 1}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    48: {
        "format": "numerical",
        "body": "If $y = y(x)$, $y \\in [0, \\pi/2)$ is the solution of the differential equation $\\sec y\\,\\dfrac{dy}{dx} - \\sin(x + y) - \\sin(x - y) = 0$, with $y(0) = 0$, then $5y'\\left(\\dfrac{\\pi}{2}\\right)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    49: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $dy = e^{\\alpha x + y}\\,dx$; $\\alpha \\in \\mathbb{N}$. If $y(\\log_{e} 2) = \\log_{e} 2$ and $y(0) = \\log_{e}(1/2)$, then the value of $\\alpha$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
