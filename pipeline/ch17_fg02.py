#!/usr/bin/env python3
"""AoD ch17 fill-gate batch 2: Q88,112,156,157,161,162."""
from ch17_push import push_repairs

REPAIRS = {
    88: {
        "format": "mcq",
        "body": "The function $f(x) = \\dfrac{4x^{3} - 3x^{2}}{6} - 2\\sin x + (2x - 1)\\cos x$",
        "options": [
            "increases in $\\left[\\dfrac{1}{2}, \\infty\\right)$",
            "decreases in $\\left(-\\infty, \\dfrac{1}{2}\\right]$",
            "decreases in $\\left[\\dfrac{1}{2}, \\infty\\right)$",
            "increases in $\\left(-\\infty, \\dfrac{1}{2}\\right]$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    112: {
        "format": "mcq",
        "body": "Let $f(x) = 3^{(x^{2} - 2)^{3} + 4}$, $x \\in R$. Then which of the following statements are true? $P$ : $x = 0$ is a point of local minima of $f$. $Q$ : $x = \\sqrt{2}$ is a point of inflection of $f$. $R$ : $f'$ is increasing for $x > \\sqrt{2}$",
        "options": [
            "Only $P$ and $Q$",
            "Only $P$ and $R$",
            "Only $Q$ and $R$",
            "All $P$, $Q$ and $R$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    156: {
        "format": "mcq",
        "body": "Let $f(x) = e^{x} - x$ and $g(x) = x^{2} - x$, $\\forall x \\in R$. Then the set of all $x \\in R$, where the function $h(x) = (fog)(x)$ is increasing, is",
        "options": [
            "$\\left[-1, -\\dfrac{1}{2}\\right] \\cup \\left[\\dfrac{1}{2}, \\infty\\right)$",
            "$[0, \\infty)$",
            "$\\left[0, \\dfrac{1}{2}\\right] \\cup [1, \\infty)$",
            "$\\left[-\\dfrac{1}{2}, 0\\right] \\cup [1, \\infty)$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    157: {
        "format": "mcq",
        "body": "Let $f(x) = \\dfrac{x}{\\sqrt{a^{2} + x^{2}}} - \\dfrac{d - x}{\\sqrt{b^{2} + (d - x)^{2}}}$, $x \\in \\mathbb{R}$ where $a$, $b$ and $d$ are non-zero real constants. Then",
        "options": [
            "$f$ is an increasing function of $x$",
            "$f$ is a decreasing function of $x$",
            "$f'$ is not a continuous function of $x$",
            "$f$ is neither increasing nor decreasing function of $x$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    161: {
        "format": "mcq",
        "body": "Let $f(x) = 4\\cos^{3} x + 3\\sqrt{3}\\cos^{2} x - 10$. The number of points of local maxima of $f$ in interval $(0, 2\\pi)$ is",
        "options": ["$3$", "$4$", "$1$", "$2$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    162: {
        "format": "numerical",
        "body": "Let the set of all positive values of $\\lambda$, for which the point of local minimum of the function $(1 + x(\\lambda^{2} - x^{2}))$ satisfies $\\dfrac{x^{2} + x + 2}{x^{2} + 5x + 6} < 0$, be $(\\alpha, \\beta)$. Then $\\alpha^{2} + \\beta^{2}$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "39",
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
