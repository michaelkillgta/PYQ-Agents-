#!/usr/bin/env python3
"""DE ch21 smash batch 2: Q139,157,183,196."""
from ch21_push import push_repairs

REPAIRS = {
    139: {
        "format": "numerical",
        "body": "Let the tangent at any point $P$ on a curve passing through the points $(1, 1)$ and $(1/10, 100)$, intersect positive $x$-axis and $y$-axis at the points $A$ and $B$ respectively. If $PA : PB = 1 : k$ and $y = y(x)$ is the solution of the differential equation $e^{\\frac{dy}{dx}} = kx + \\dfrac{k}{2}$, $y(0) = k$, then $4y(1) - 5\\log_{e} 3$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "5",
    },
    157: {
        "format": "mcq",
        "body": "Let the solution curve $y = y(x)$ of the differential equation $\\left[\\dfrac{x}{\\sqrt{x^{2} - y^{2}}} + e^{y/x}\\right] x\\dfrac{dy}{dx} = x + \\left[\\dfrac{x}{\\sqrt{x^{2} - y^{2}}} + e^{y/x}\\right] y$ pass through the points $(1, 0)$ and $(2\\alpha, \\alpha)$, $\\alpha > 0$. Then $\\alpha$ is equal to",
        "options": [
            "$\\dfrac{1}{2}\\exp\\left(\\dfrac{\\pi}{6} + \\sqrt{e} - 1\\right)$",
            "$\\dfrac{1}{2}\\exp\\left(\\dfrac{\\pi}{3} + \\sqrt{e} - 1\\right)$",
            "$\\exp\\left(\\dfrac{\\pi}{6} + \\sqrt{e} + 1\\right)$",
            "$2\\exp\\left(\\dfrac{\\pi}{3} + \\sqrt{e} - 1\\right)$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    183: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\cos x(3\\sin x + \\cos x + 3)\\,dy = (1 + y\\sin x(3\\sin x + \\cos x + 3))\\,dx$, $0 \\le x \\le \\pi/2$, $y(0) = 0$. Then $y(\\pi/3)$ is equal to",
        "options": [
            "$2\\log_{e}\\left(\\dfrac{2\\sqrt{3} + 9}{6}\\right)$",
            "$2\\log_{e}\\left(\\dfrac{2\\sqrt{3} + 10}{11}\\right)$",
            "$2\\log_{e}\\left(\\dfrac{\\sqrt{3} + 7}{2}\\right)$",
            "$2\\log_{e}\\left(\\dfrac{3\\sqrt{3} - 8}{4}\\right)$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    196: {
        "format": "mcq",
        "body": "Let the slope of the tangent to a curve $y = f(x)$ at $(x, y)$ be given by $2\\tan x(\\cos x - y)$. If the curve passes through the point $(\\pi/4, 0)$, then the value of $\\int_{0}^{\\pi/2} y\\,dx$ is equal to",
        "options": [
            "$(2 - \\sqrt{2}) + \\dfrac{\\pi}{\\sqrt{2}}$",
            "$2 - \\dfrac{\\pi}{\\sqrt{2}}$",
            "$(2 + \\sqrt{2}) + \\dfrac{\\pi}{\\sqrt{2}}$",
            "$2 + \\dfrac{\\pi}{\\sqrt{2}}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
