#!/usr/bin/env python3
"""AoD ch17 fill-gate batch 1: Q15,16,21,63,65,69."""
from ch17_push import push_repairs

REPAIRS = {
    15: {
        "format": "mcq",
        "body": "Let $f(x) = 3\\sin^{4} x + 10\\sin^{3} x + 6\\sin^{2} x - 3$, $x \\in \\left[-\\dfrac{\\pi}{6}, \\dfrac{\\pi}{2}\\right]$. Then, $f$ is",
        "options": [
            "increasing in $\\left(-\\dfrac{\\pi}{6}, \\dfrac{\\pi}{2}\\right)$",
            "decreasing in $\\left(0, \\dfrac{\\pi}{2}\\right)$",
            "increasing in $\\left(-\\dfrac{\\pi}{6}, 0\\right)$",
            "decreasing in $\\left(-\\dfrac{\\pi}{6}, 0\\right)$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    16: {
        "format": "mcq",
        "body": "If $x = 1$ is a critical point of the function $f(x) = (3x^{2} + ax - 2 - a)e^{x}$, then",
        "options": [
            "$x = 1$ and $x = -\\dfrac{2}{3}$ are local minima of $f$",
            "$x = 1$ and $x = -\\dfrac{2}{3}$ is a local maxima of $f$",
            "$x = 1$ is a local maxima and $x = -\\dfrac{2}{3}$ is a local minima of $f$",
            "$x = 1$ is a local minima and $x = -\\dfrac{2}{3}$ are local maxima of $f$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    21: {
        "format": "mcq",
        "body": "The function $f(x) = 2x + 3x^{\\frac{2}{3}}$, $x \\in R$, has",
        "options": [
            "exactly one point of local minima and no point of local maxima",
            "exactly one point of local maxima and no point of local minima",
            "exactly one point of local maxima and exactly one point of local minima",
            "exactly two points of local maxima and exactly one point of local minima",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    63: {
        "format": "mcq",
        "body": "Let $f : R \\to R$ be a function defined by $f(x) = \\bigl||x + 2| - 2|x|\\bigr|$. If $m$ is the number of points of local minima and $n$ is the number of points of local maxima of $f$, then $m + n$ is",
        "options": ["$5$", "$3$", "$2$", "$4$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    65: {
        "format": "mcq",
        "body": "Let $(2, 3)$ be the largest open interval in which the function $f(x) = 2\\log_{e}(x - 2) - x^{2} + ax + 1$ is strictly increasing and $(b, c)$ be the largest open interval, in which the function $g(x) = (x - 1)^{3}(x + 2 - a)^{2}$ is strictly decreasing. Then $100(a + b - c)$ is equal to",
        "options": ["$420$", "$360$", "$160$", "$280$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    69: {
        "format": "mcq",
        "body": "The function $f(x) = \\dfrac{x}{x^{2} - 6x - 16}$, $x \\in \\mathbb{R} - \\{-2, 8\\}$",
        "options": [
            "decreases in $(-2, 8)$ and increases in $(-\\infty, -2) \\cup (8, \\infty)$",
            "decreases in $(-\\infty, -2) \\cup (-2, 8) \\cup (8, \\infty)$",
            "decreases in $(-\\infty, -2)$ and increases in $(8, \\infty)$",
            "increases in $(-\\infty, -2) \\cup (-2, 8) \\cup (8, \\infty)$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
