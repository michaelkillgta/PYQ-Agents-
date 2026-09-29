#!/usr/bin/env python3
"""AoD smashed stems: Q64,66,76,140,168,173."""
from ch17_push import push_repairs

REPAIRS = {
    64: {
        "format": "mcq",
        "body": "Let the function $f(x) = \\dfrac{x}{3} + \\dfrac{3}{x} + 3$, $x \\neq 0$ be strictly increasing in $(-\\infty, \\alpha_{1}) \\cup (\\alpha_{2}, \\infty)$ and strictly decreasing in $(\\alpha_{3}, \\alpha_{4}) \\cup (\\alpha_{4}, \\alpha_{5})$. Then $\\sum_{i=1}^{5} \\alpha_{i}^{2}$ is equal to",
        "options": ["$48$", "$28$", "$40$", "$36$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    66: {
        "format": "mcq",
        "body": "For the function $f(x) = (\\cos x) - x + 1$, $x \\in \\mathbb{R}$, between the following two statements (S1) $f(x) = 0$ for only one value of $x$ in $[0, \\pi]$. (S2) $f(x)$ is decreasing in $\\left[0, \\dfrac{\\pi}{2}\\right]$ and increasing in $\\left[\\dfrac{\\pi}{2}, \\pi\\right]$.",
        "options": [
            "Both (S1) and (S2) are correct.",
            "Both (S1) and (S2) are incorrect.",
            "Only (S2) is correct.",
            "Only (S1) is correct.",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    76: {
        "format": "mcq",
        "body": "The function $f(x) = xe^{x(1 - x)}$, $x \\in R$, is",
        "options": [
            "increasing in $\\left(-\\dfrac{1}{2}, 1\\right)$",
            "decreasing in $\\left(\\dfrac{1}{2}, 2\\right)$",
            "increasing in $\\left(-1, -\\dfrac{1}{2}\\right)$",
            "decreasing in $\\left(-\\dfrac{1}{2}, \\dfrac{1}{2}\\right)$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    140: {
        "format": "mcq",
        "body": "The number of points on the curve $y = 54x^{5} - 135x^{4} - 70x^{3} + 180x^{2} + 210x$ at which the normal lines are parallel to $x + 90y + 2 = 0$ is",
        "options": ["$2$", "$3$", "$4$", "$0$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    168: {
        "format": "mcq",
        "body": "Let $f : R \\to R$ be a function defined by $f(x) = (x - 3)^{n_{1}}(x - 5)^{n_{2}}$, $n_{1}$, $n_{2} \\in N$. Then, which of the following is NOT true?",
        "options": [
            "For $n_{1} = 3$, $n_{2} = 4$, there exists $\\alpha \\in (3, 5)$ where $f$ attains local maxima.",
            "For $n_{1} = 4$, $n_{2} = 3$, there exists $\\alpha \\in (3, 5)$ where $f$ attains local maxima.",
            "For $n_{1} = 3$, $n_{2} = 5$, there exists $\\alpha \\in (3, 5)$ where $f$ attains local maxima.",
            "For $n_{1} = 4$, $n_{2} = 6$, there exists $\\alpha \\in (3, 5)$ where $f$ attains local maxima.",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    173: {
        "format": "mcq",
        "body": "Let $f(x)$ be a polynomial of degree $5$ such that $x = \\pm 1$ are its critical points. If $\\displaystyle\\lim_{x \\to 0}\\left(2 + \\dfrac{f(x)}{x^{3}}\\right) = 4$, then which one of the following is not true?",
        "options": [
            "$f$ is an odd function",
            "$f(1) - 4f(-1) = 4$. $x = 1$ is a point of maximum and $x = -1$",
            "$x = 1$ is a point of local minimum and $x = -1$ is a point of local maximum",
            "$x = 1$ is a point of local maxima of $f$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
