#!/usr/bin/env python3
"""AoD ch17 fill leftover: Q170-172,174."""
from ch17_push import push_repairs

REPAIRS = {
    170: {
        "format": "numerical",
        "body": "If a rectangle is inscribed in an equilateral triangle of side length $2\\sqrt{2}$ as shown in the figure, then the square of the largest area of such a rectangle is _________.\n\n[[fig:p163_x1135]]",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    171: {
        "format": "numerical",
        "body": "Let $P(x)$ be a real polynomial of degree $3$ which vanishes at $x = -3$. Let $P(x)$ have local minima at $x = 1$, local maxima at $x = -1$ and $\\int_{-1}^{1} P(x)\\, dx = 18$, then the sum of all the coefficients of the polynomial $P(x)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "8",
    },
    172: {
        "format": "numerical",
        "body": "Let $f(x)$ be a polynomial of degree $6$ in $x$, in which the coefficient of $x^{6}$ is unity and it has extrema at $x = -1$ and $x = 1$. If $\\displaystyle\\lim_{x \\to 0} \\dfrac{f(x)}{x^{3}} = 1$, then $5 \\cdot f(2)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "144",
    },
    174: {
        "format": "mcq",
        "body": "Let $f(x) = 5 - |x - 2|$ and $g(x) = |x + 1|$, $x \\in R$. If $f(x)$ attains maximum value at $\\alpha$ and $g(x)$ attains minimum value at $\\beta$, then $\\displaystyle\\lim_{x \\to -\\alpha\\beta} \\dfrac{(x - 1)(x^{2} - 5x + 6)}{x^{2} - 6x + 8}$ is equal to",
        "options": [
            "$\\dfrac{3}{2}$",
            "$\\dfrac{1}{2}$",
            "$-\\dfrac{3}{2}$",
            "$-\\dfrac{1}{2}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
