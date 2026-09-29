#!/usr/bin/env python3
"""DE ch21 fill-gate batch C: Q69,82,91,98,100,105."""
from ch21_push import push_repairs

REPAIRS = {
    69: {
        "format": "mcq",
        "body": "Let $f(x) = x - 1$ and $g(x) = e^{x}$ for $x \\in \\mathbb{R}$. If $\\dfrac{dy}{dx} = \\left(e^{-2\\sqrt{x}} g(f(f(x))) - \\dfrac{y}{\\sqrt{x}}\\right)$, $y(0) = 0$, then $y(1)$ is",
        "options": [
            "$\\dfrac{1 - e^{2}}{e^{4}}$",
            "$\\dfrac{2e - 1}{e^{3}}$",
            "$\\dfrac{e - 1}{e^{4}}$",
            "$\\dfrac{1 - e^{3}}{e^{4}}$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    82: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} = 2x(x + y)^{3} - x(x + y) - 1$, $y(0) = 1$. Then $\\left(\\dfrac{1}{\\sqrt{2}} + y\\left(\\dfrac{1}{\\sqrt{2}}\\right)\\right)^{2}$ equals",
        "options": [
            "$\\dfrac{4}{4 + \\sqrt{e}}$",
            "$\\dfrac{3}{3 - \\sqrt{e}}$",
            "$\\dfrac{2}{1 + \\sqrt{e}}$",
            "$\\dfrac{1}{2 - \\sqrt{e}}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    91: {
        "format": "mcq",
        "body": "Let $y = y(x)$, $y > 0$, be a solution curve of the differential equation $(1 + x^{2})\\,dy = y(x - y)\\,dx$. If $y(0) = 1$ and $y(2\\sqrt{2}) = \\beta$, then which of the following is true",
        "options": [
            "$e^{3\\beta - 1} = e(3 + 2\\sqrt{2})$",
            "$e^{3\\beta - 1} = e(5 + \\sqrt{2})$",
            "$e^{\\beta - 1} = e^{-2}(3 + 2\\sqrt{2})$",
            "$e^{\\beta - 1} = e^{-2}(5 + \\sqrt{2})$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    98: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution curve of the differential equation $\\dfrac{dy}{dx} + \\dfrac{1}{x^{2} - 1} y = \\left(\\dfrac{x - 1}{x + 1}\\right)^{1/2}$, $x > 1$ passing through the point $\\left(2, \\sqrt{1/3}\\right)$. Then $\\sqrt{7} y(8)$ is equal to",
        "options": [
            "$11 + 6\\log_{e} 3$",
            "$19$",
            "$12 - 2\\log_{e} 3$",
            "$19 - 6\\log_{e} 3$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    100: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution curve of the differential equation $\\dfrac{dy}{dx} + \\left(\\dfrac{2x^{2} + 11x + 13}{x^{3} + 6x^{2} + 11x + 6}\\right)y = \\dfrac{x + 3}{x + 1}$, $x > -1$, which passes through the point $(0, 1)$. Then $y(1)$ is equal to",
        "options": ["$\\dfrac{1}{2}$", "$\\dfrac{3}{2}$", "$\\dfrac{5}{2}$", "$\\dfrac{7}{2}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    105: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation $x\\dfrac{dy}{dx} + 2y = x e^{x}$, $y(1) = 0$ then the local maximum value of the function $z(x) = x^{2} y(x) - e^{x}$, $x \\in \\mathbb{R}$ is",
        "options": ["$1 - e$", "$0$", "$\\dfrac{1}{2}$", "$\\dfrac{4}{e} - e$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
