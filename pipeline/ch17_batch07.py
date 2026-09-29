#!/usr/bin/env python3
"""AoD ch17 held batch 7: Q167,170,175-178."""
from ch17_push import push_repairs

REPAIRS = {
    167: {
        "format": "numerical",
        "body": "Let $f(x) = |(x - 1)(x^{2} - 2x - 3)| + x - 3$, $x \\in \\mathbb{R}$. If $m$ and $M$ are respectively the number of points of local minimum and local maximum of $f$ in the interval $(0, 4)$, then $m + M$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    170: {
        "format": "numerical",
        "body": "If a rectangle is inscribed in an equilateral triangle of side length $2\\sqrt{2}$ as shown in the figure, then the square of the largest area of such a rectangle is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    175: {
        "format": "numerical",
        "body": "Let $f : \\mathbb{R} \\to \\mathbb{R}$ be a thrice differentiable function such that $f(0) = 0$, $f(1) = 1$, $f(2) = -1$, $f(3) = 2$ and $f(4) = -2$. Then, the minimum number of zeros of $(3f'f'' + ff''')(x)$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "5",
    },
    176: {
        "format": "numerical",
        "body": "Let $f : [0, 1] \\to R$ be a twice differentiable function in $(0, 1)$ such that $f(0) = 3$ and $f(1) = 5$. If the line $y = 2x + 3$ intersects the graph of $f$ at only two distinct points in $(0, 1)$, then the least number of points $x \\in (0, 1)$, at which $f''(x) = 0$, is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    177: {
        "format": "numerical",
        "body": "Let $f$ and $g$ be twice differentiable even functions on $(-2, 2)$ such that $f\\left(\\dfrac{1}{4}\\right) = 0$, $f\\left(\\dfrac{1}{2}\\right) = 0$, $f(1) = 1$ and $g\\left(\\dfrac{3}{4}\\right) = 0$, $g(1) = 2$. Then, the minimum number of solutions of $f(x)g''(x) + f'(x)g''(x) = 0$ in $(-2, 2)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    178: {
        "format": "mcq",
        "body": "Let $f$ be any continuous function on $[0, 2]$ and twice differentiable on $(0, 2)$. If $f(0) = 0$, $f(1) = 1$ and $f(2) = 2$, then",
        "options": [
            "$f''(x) > 0$ for all $x \\in (0, 2)$",
            "$f'(x) = 0$ for some $x \\in (0, 2)$",
            "$f''(x) = 0$ for some $x \\in (0, 2)$",
            "$f''(x) = 0$ for all $x \\in (0, 2)$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
