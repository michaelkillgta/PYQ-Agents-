#!/usr/bin/env python3
"""AoD leftover smash: Q24,91,113,126,130,166."""
from ch17_push import push_repairs

REPAIRS = {
    24: {
        "format": "mcq",
        "body": "$\\displaystyle\\max_{0 \\leq x \\leq \\pi}\\left\\{x - 2\\sin x \\cos x + \\dfrac{1}{3}\\sin 3x\\right\\}$ is equal to",
        "options": [
            "$\\dfrac{\\pi + 2 - 3\\sqrt{3}}{6}$",
            "$\\pi$",
            "$0$",
            "$\\dfrac{5\\pi + 2 + 3\\sqrt{3}}{6}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    91: {
        "format": "numerical",
        "body": "Let $a$ be an integer such that all the real roots of the polynomial $2x^{5} + 5x^{4} + 10x^{3} + 10x^{2} + 10x + 10$ lie in the interval $(a, a + 1)$. Then, $|a|$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    113: {
        "format": "mcq",
        "body": "The sum of the absolute minimum and the absolute maximum values of the function $f(x) = |3x - x^{2} + 2| - x$ in the interval $[-1, 2]$ is",
        "options": [
            "$\\dfrac{\\sqrt{17} + 3}{2}$",
            "$\\dfrac{\\sqrt{17} + 5}{2}$",
            "$5$",
            "$\\dfrac{9 - \\sqrt{17}}{2}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    126: {
        "format": "mcq",
        "body": "If $p(x)$ be a polynomial of degree three that has a local maximum value $8$ at $x = 1$ and a local minimum value $4$ at $x = 2$ then $p(0)$ is equal to",
        "options": ["$6$", "$-12$", "$24$", "$12$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    130: {
        "format": "mcq",
        "body": "If $S_{1}$ and $S_{2}$ are respectively the sets of local minimum and local maximum points of the function $f(x) = 9x^{4} + 12x^{3} - 36x^{2} + 25$, $x \\in R$, then",
        "options": [
            "$S_{1} = \\{-2\\}$; $S_{2} = \\{0, 1\\}$",
            "$S_{1} = \\{-1\\}$; $S_{2} = \\{0, 2\\}$",
            "$S_{1} = \\{-2, 0\\}$; $S_{2} = \\{1\\}$",
            "$S_{1} = \\{-2, 1\\}$; $S_{2} = \\{0\\}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    166: {
        "format": "mcq",
        "body": "The sum of absolute maximum and absolute minimum values of the function $f(x) = |2x^{2} + 3x - 2| + \\sin x \\cos x$ in the interval $[0, 1]$ is",
        "options": [
            "$3 + \\dfrac{\\sin(1)\\cos^{2}\\left(\\dfrac{1}{2}\\right)}{2}$",
            "$3 + \\dfrac{1}{2}(1 + 2\\cos(1))\\sin(1)$",
            "$5 + \\dfrac{1}{2}(\\sin(1) + \\sin(2))$",
            "$2 + \\sin\\left(\\dfrac{1}{2}\\right)\\cos\\left(\\dfrac{1}{2}\\right)$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
