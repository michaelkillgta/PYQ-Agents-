#!/usr/bin/env python3
"""DE ch21 fill-gate batch E: Q156,159,160,175,178,185,195."""
from ch21_push import push_repairs

REPAIRS = {
    156: {
        "format": "mcq",
        "body": "If the solution curve $y = y(x)$ of the differential equation $y^{2}\\,dx + (x^{2} - xy + y^{2})\\,dy = 0$, which passes through the point $(1, 1)$ and intersects the line $y = \\sqrt{3}x$ at the point $(\\alpha, \\sqrt{3}\\alpha)$, then the value of $\\log_{e}(\\sqrt{3}\\alpha)$ is equal to",
        "options": ["$\\dfrac{\\pi}{2}$", "$\\dfrac{\\pi}{4}$", "$\\dfrac{\\pi}{6}$", "$\\dfrac{\\pi}{12}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    159: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $x\\tan(y/x)\\,dy = (y\\tan(y/x) - x)\\,dx$, $-1 \\le x \\le 1$, $y(1/2) = \\pi/6$. Then the area of the region bounded by the curves $x = 0$, $x = 1/\\sqrt{2}$ and $y = y(x)$ in the upper half plane is",
        "options": [
            "$\\dfrac{1}{8}(\\pi - 1)$",
            "$\\dfrac{1}{12}(\\pi - 3)$",
            "$\\dfrac{1}{4}(\\pi - 2)$",
            "$\\dfrac{1}{6}(\\pi - 1)$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    160: {
        "format": "mcq",
        "body": "Let $C_{1}$ be the curve obtained by the solution of differential equation $2xy\\dfrac{dy}{dx} = y^{2} - x^{2}$, $x > 0$. Let the curve $C_{2}$ be the solution of $\\dfrac{2xy}{x^{2} - y^{2}} = \\dfrac{dy}{dx}$. If both the curves pass through $(1, 1)$, then the area (in sq. units) enclosed by the curves $C_{1}$ and $C_{2}$ is equal to",
        "options": ["$\\pi - 1$", "$\\dfrac{\\pi}{2} - 1$", "$\\pi + 1$", "$\\dfrac{\\pi}{4} + 1$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    175: {
        "format": "mcq",
        "body": "Let the solution curve $y = y(x)$ of the differential equation $\\dfrac{dy}{dx} - \\dfrac{3x^{5}\\tan^{-1}(x^{3})}{(1 + x^{6})^{3/2}} y = 2x\\exp\\left(\\dfrac{x^{3} - \\tan^{-1}(x^{3})}{\\sqrt{1 + x^{6}}}\\right)$ pass through the origin. Then $y(1)$ is equal to",
        "options": [
            "$\\exp\\left(\\dfrac{4 - \\pi}{4\\sqrt{2}}\\right)$",
            "$\\exp\\left(\\dfrac{\\pi - 4}{4\\sqrt{2}}\\right)$",
            "$\\exp\\left(\\dfrac{1 - \\pi}{4\\sqrt{2}}\\right)$",
            "$\\exp\\left(\\dfrac{4 + \\pi}{4\\sqrt{2}}\\right)$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    178: {
        "format": "mcq",
        "body": "Let the solution curve $y = f(x)$ of the differential equation $\\dfrac{dy}{dx} + \\dfrac{xy}{x^{2} - 1} = \\dfrac{x^{4} + 2x}{\\sqrt{1 - x^{2}}}$, $x \\in (-1, 1)$ pass through the origin. Then $\\displaystyle\\int_{-\\sqrt{3}/2}^{\\sqrt{3}/2} f(x)\\,dx$ is equal to",
        "options": [
            "$\\dfrac{\\pi}{3} - \\dfrac{1}{4}$",
            "$\\dfrac{\\pi}{3} - \\dfrac{\\sqrt{3}}{4}$",
            "$\\dfrac{\\pi}{6} - \\dfrac{\\sqrt{3}}{4}$",
            "$\\dfrac{\\pi}{6} - \\dfrac{\\sqrt{3}}{2}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    185: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} = (y + 1)\\left((y + 1)e^{x^{2}/2} - x\\right)$, $0 < x < 2$, with $y(2) = 0$. Then the value of $\\dfrac{dy}{dx}$ at $x = 1$ is equal to",
        "options": [
            "$\\dfrac{-e^{3/2}}{(e^{2} + 1)^{2}}$",
            "$-\\dfrac{2e^{2}}{(1 + e^{2})^{2}}$",
            "$\\dfrac{e^{5/2}}{(1 + e^{2})^{2}}$",
            "$\\dfrac{5e^{1/2}}{(e^{2} + 1)^{2}}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    195: {
        "format": "mcq",
        "body": "Let $f(x)$ be a positive function such that the area bounded by $y = f(x)$, $y = 0$ from $x = 0$ to $x = a > 0$ is $e^{-a} + 4a^{2} + a - 1$. Then the differential equation, whose general solution is $y = c_{1} f(x) + c_{2}$, where $c_{1}$ and $c_{2}$ are arbitrary constants, is which of the following",
        "options": [
            "$(8e^{x} - 1)\\dfrac{d^{2}y}{dx^{2}} + \\dfrac{dy}{dx} = 0$",
            "$(8e^{x} - 1)\\dfrac{d^{2}y}{dx^{2}} - \\dfrac{dy}{dx} = 0$",
            "$(8e^{x} + 1)\\dfrac{d^{2}y}{dx^{2}} - \\dfrac{dy}{dx} = 0$",
            "$(8e^{x} + 1)\\dfrac{d^{2}y}{dx^{2}} + \\dfrac{dy}{dx} = 0$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
