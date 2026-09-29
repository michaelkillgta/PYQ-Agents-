#!/usr/bin/env python3
"""AoD ch17 held batch 5: Q58-62,116."""
from ch17_push import push_repairs

REPAIRS = {
    58: {
        "format": "mcq",
        "body": "If the tangent to the curve $y = \\dfrac{x}{x^{2} - 3}$, $x \\in R$, $\\left(x \\neq \\pm\\sqrt{3}\\right)$, at a point $(\\alpha, \\beta) \\neq (0, 0)$ on it is parallel to the line $2x + 6y - 11 = 0$, then",
        "options": [
            "$|2\\alpha + 6\\beta| = 19$",
            "$|2\\alpha + 6\\beta| = 11$",
            "$|6\\alpha + 2\\beta| = 19$",
            "$|6\\alpha + 2\\beta| = 9$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    59: {
        "format": "mcq",
        "body": "If $\\theta$ denotes the acute angle between the curves $y = 10 - x^{2}$ and $y = 2 + x^{2}$ at a point of their intersection, then $|\\tan \\theta|$ is equal to",
        "options": ["$\\dfrac{4}{9}$", "$\\dfrac{8}{17}$", "$\\dfrac{7}{17}$", "$\\dfrac{8}{15}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    60: {
        "format": "mcq",
        "body": "The shortest distance between the point $\\left(\\dfrac{3}{2}, 0\\right)$ and the curve $y = \\sqrt{x}$, $(x > 0)$, is",
        "options": ["$\\dfrac{\\sqrt{3}}{2}$", "$\\dfrac{5}{4}$", "$\\dfrac{3}{2}$", "$\\dfrac{\\sqrt{5}}{2}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    61: {
        "format": "mcq",
        "body": "The tangent to the curve $y = xe^{x^{2}}$ passing through the point $(1, e)$ also passes through the point",
        "options": [
            "$\\left(\\dfrac{4}{3}, 2e\\right)$",
            "$(2, 3e)$",
            "$\\left(\\dfrac{5}{3}, 2e\\right)$",
            "$(3, 6e)$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    62: {
        "format": "mcq",
        "body": "The tangent to the curve $y = x^{2} - 5x + 5$, parallel to the line $2y = 4x + 1$, also passes through the point",
        "options": [
            "$\\left(\\dfrac{1}{4}, \\dfrac{7}{2}\\right)$",
            "$\\left(\\dfrac{7}{2}, \\dfrac{1}{4}\\right)$",
            "$\\left(-\\dfrac{1}{8}, 7\\right)$",
            "$\\left(\\dfrac{1}{8}, -7\\right)$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    116: {
        "format": "mcq",
        "body": "A wire of length $22$ m is to be cut into two pieces. One of the pieces is to be made into a square and the other into an equilateral triangle. Then, the length of the side of the equilateral triangle, so that the combined area of the square and the equilateral triangle is minimum, is",
        "options": [
            "$\\dfrac{22}{9 + 4\\sqrt{3}}$",
            "$\\dfrac{66}{9 + 4\\sqrt{3}}$",
            "$\\dfrac{22}{4 + 9\\sqrt{3}}$",
            "$\\dfrac{66}{4 + 9\\sqrt{3}}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
