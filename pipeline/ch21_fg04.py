#!/usr/bin/env python3
"""DE ch21 fill-gate batch D: Q111,115,146,152,153,154."""
from ch21_push import push_repairs

REPAIRS = {
    111: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} = 2(y + 2\\sin x - 5)x - 2\\cos x$ such that $y(0) = 7$. Then $y(\\pi)$ is equal to",
        "options": ["$7e^{\\pi^{2}} + 5$", "$e^{\\pi^{2}} + 5$", "$2e^{\\pi^{2}} + 5$", "$3e^{\\pi^{2}} + 5$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    115: {
        "format": "mcq",
        "body": "If a curve passes through the origin and the slope of the tangent to it at any point $(x, y)$ is $\\dfrac{x^{2} - 4x + y + 8}{x - 2}$, then this curve also passes through which of the following points",
        "options": ["$(5, 4)$", "$(4, 4)$", "$(4, 5)$", "$(5, 5)$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    146: {
        "format": "mcq",
        "body": "Given that the slope of the tangent to a curve $y = y(x)$ at any point $(x, y)$ is $\\dfrac{2y}{x^{2}}$. If the curve passes through the centre of the circle $x^{2} + y^{2} - 2x - 2y = 0$, then its equation is",
        "options": [
            "$x^{2}\\log_{e}|y| = -2(x - 1)$",
            "$x\\log_{e}|y| = 2(x - 1)$",
            "$x\\log_{e}|y| = -2(x - 1)$",
            "$x\\log_{e}|y| = x - 1$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    152: {
        "format": "mcq",
        "body": "The general solution of the differential equation $\\sqrt{1 + x^{2} + y^{2} + x^{2}y^{2}} + xy\\dfrac{dy}{dx} = 0$ (where $C$ is a constant of integration) is which of the following",
        "options": [
            "$\\sqrt{1 + y^{2}} + \\sqrt{1 + x^{2}} = \\dfrac{1}{2}\\log_{e}\\left(\\dfrac{\\sqrt{1 + x^{2}} - 1}{\\sqrt{1 + x^{2}} + 1}\\right) + C$",
            "$\\sqrt{1 + y^{2}} - \\sqrt{1 + x^{2}} = \\dfrac{1}{2}\\log_{e}\\left(\\dfrac{\\sqrt{1 + x^{2}} - 1}{\\sqrt{1 + x^{2}} + 1}\\right) + C$",
            "$\\sqrt{1 + y^{2}} + \\sqrt{1 + x^{2}} = \\dfrac{1}{2}\\log_{e}\\left(\\dfrac{\\sqrt{1 + x^{2}} + 1}{\\sqrt{1 + x^{2}} - 1}\\right) + C$",
            "$\\sqrt{1 + y^{2}} - \\sqrt{1 + x^{2}} = \\dfrac{1}{2}\\log_{e}\\left(\\dfrac{\\sqrt{1 + x^{2}} + 1}{\\sqrt{1 + x^{2}} - 1}\\right) + C$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    153: {
        "format": "mcq",
        "body": "Let $f(x) = \\left(\\sin(\\tan^{-1} x) + \\sin(\\cot^{-1} x)\\right)^{2} - 1$, $|x| > 1$. If $\\dfrac{dy}{dx} = \\dfrac{1}{2}\\dfrac{d}{dx}(\\sin^{-1}(f(x)))$ and $y(\\sqrt{3}) = \\pi/6$, then $y(-\\sqrt{3})$ is equal to",
        "options": ["$\\dfrac{2\\pi}{3}$", "$-\\dfrac{\\pi}{6}$", "$\\dfrac{5\\pi}{6}$", "$\\dfrac{\\pi}{3}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    154: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(x + y + 2)^{2}\\,dx = dy$, $y(0) = -2$. Let the maximum and minimum values of the function $y = y(x)$ in $[0, \\pi/3]$ be $\\alpha$ and $\\beta$, respectively. If $(3\\alpha + \\pi)^{2} + \\beta^{2} = \\gamma + \\delta\\sqrt{3}$, $\\gamma, \\delta \\in \\mathbb{Z}$, then $\\gamma + \\delta$ equals _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "31",
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
