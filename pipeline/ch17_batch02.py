#!/usr/bin/env python3
"""AoD ch17 held batch 2: Q9-14."""
from ch17_push import push_repairs

REPAIRS = {
    9: {
        "format": "numerical",
        "body": "Let the normals at all the points on a given curve pass through a fixed point $(a, b)$. If the curve passes through $(3, -3)$ and $(4, -2\\sqrt{2})$, given that $a - 2\\sqrt{2}\\, b = 3$, then $(a^{2} + b^{2} + ab)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "9",
    },
    10: {
        "format": "mcq",
        "body": "Which of the following points lies on the tangent to the curve $x^{4}e^{y} + 2\\sqrt{y + 1} = 3$ at the point $(1, 0)$",
        "options": ["$(2, 2)$", "$(2, 6)$", "$(-2, 6)$", "$(-2, 4)$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    11: {
        "format": "mcq",
        "body": "The length of the perpendicular from the origin, on normal to the curve, $x^{2} + 2xy - 3y^{2} = 0$, at the point $(2, 2)$, is",
        "options": ["$\\sqrt{2}$", "$4\\sqrt{2}$", "$2$", "$2\\sqrt{2}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    12: {
        "format": "mcq",
        "body": "The shortest distance between the line $y = x$ and the curve $y^{2} = x - 2$ is",
        "options": ["$\\dfrac{7}{4\\sqrt{2}}$", "$\\dfrac{7}{8}$", "$\\dfrac{11}{4\\sqrt{2}}$", "$2$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    13: {
        "format": "mcq",
        "body": "Let $S$ be the set of all values of $x$ for which the tangent to the curve $y = f(x) = x^{3} - x^{2} - 2x$ at $(x, y)$ is parallel to the line segment joining the points $(1, f(1))$ and $(-1, f(-1))$, then $S$ is equal to",
        "options": [
            "$\\left\\{-\\dfrac{1}{3}, -1\\right\\}$",
            "$\\left\\{-\\dfrac{1}{3}, 1\\right\\}$",
            "$\\left\\{\\dfrac{1}{3}, 1\\right\\}$",
            "$\\left\\{\\dfrac{1}{3}, -1\\right\\}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    14: {
        "format": "numerical",
        "body": "The number of distinct real roots of the equation $3x^{4} + 4x^{3} - 12x^{2} + 4 = 0$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
