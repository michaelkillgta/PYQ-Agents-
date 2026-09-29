#!/usr/bin/env python3
"""AoD ch17 held batch 6: Q118,120,123,127,141,160."""
from ch17_push import push_repairs

REPAIRS = {
    118: {
        "format": "mcq",
        "body": "A wire of length $20$ m is to be cut into two pieces. One of the pieces is to be made into a square and the other into a regular hexagon. Then the length of the side (in meters) of the hexagon, so that the combined area of the square and the hexagon is minimum, is",
        "options": [
            "$\\dfrac{10}{2 + 3\\sqrt{3}}$",
            "$\\dfrac{5}{3 + \\sqrt{3}}$",
            "$\\dfrac{10}{3 + 2\\sqrt{3}}$",
            "$\\dfrac{5}{2 + \\sqrt{3}}$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    120: {
        "format": "mcq",
        "body": "Let $M$ and $m$ respectively be the maximum and minimum values of the function $f(x) = \\tan^{-1}(\\sin x + \\cos x)$ in $\\left[0, \\dfrac{\\pi}{2}\\right]$. Then the value of $\\tan(M - m)$ is equal to",
        "options": ["$2 - \\sqrt{3}$", "$3 - 2\\sqrt{2}$", "$3 + 2\\sqrt{2}$", "$2 + \\sqrt{3}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    123: {
        "format": "numerical",
        "body": "The maximum value of $z$ in the following equation $z = 6xy + y^{2}$, where $3x + 4y \\leq 100$ and $4x + 3y \\leq 75$ for $x \\geq 0$ and $y \\geq 0$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "904",
    },
    127: {
        "format": "numerical",
        "body": "Let $AD$ and $BC$ be two vertical poles at $A$ and $B$ respectively on a horizontal ground. If $AD = 8$ m, $BC = 11$ m, $AB = 10$ m; then the distance (in meters) of a point $M$ lying in between $AB$ from the point $A$ such that $MD^{2} + MC^{2}$ is minimum, is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "5",
    },
    141: {
        "format": "numerical",
        "body": "Let the area enclosed by the $x$-axis, and the tangent and normal drawn to the curve $4x^{3} - 3xy^{2} + 6x^{2} - 5xy - 8y^{2} + 9x + 14 = 0$ at the point $(-2, 3)$ be $A$. Then $8A$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "170",
    },
    160: {
        "format": "mcq",
        "body": "The sum of all local minimum values of the function $f(x) = \\begin{cases} 1 - 2x, & x < -1 \\\\ \\dfrac{1}{3}(7 + 2|x|), & -1 \\leq x \\leq 2 \\\\ \\dfrac{11}{18}(x - 4)(x - 5), & x > 2 \\end{cases}$ is",
        "options": ["$\\dfrac{157}{72}$", "$\\dfrac{131}{72}$", "$\\dfrac{171}{72}$", "$\\dfrac{167}{72}$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
