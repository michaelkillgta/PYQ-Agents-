#!/usr/bin/env python3
"""AoD ch17 held batch 8: Q179-183."""
from ch17_push import push_repairs

REPAIRS = {
    179: {
        "format": "mcq",
        "body": "Let $f : (a, b) \\to R$ be twice differentiable function such that $f(x) = \\int_{a}^{x} g(t)\\, dt$ for a differentiable function $g(x)$. If $f(x) = 0$ has exactly five distinct roots in $(a, b)$, then $g(x)g'(x) = 0$ has at least",
        "options": [
            "twelve roots in $(a, b)$",
            "five roots in $(a, b)$",
            "seven roots in $(a, b)$",
            "three roots in $(a, b)$",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    180: {
        "format": "mcq",
        "body": "Let $f$ be a twice differentiable function on $(1, 6)$. If $f(2) = 8$, $f'(2) = 5$, $f'(x) \\geq 1$ and $f''(x) \\geq 4$, for all $x \\in (1, 6)$, then",
        "options": [
            "$f(5) + f'(5) \\leq 26$",
            "$f(5) + f'(5) \\geq 28$",
            "$f'(5) + f''(5) \\leq 20$",
            "$f(5) \\leq 10$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    181: {
        "format": "mcq",
        "body": "For all twice differentiable functions $f : \\mathbf{R} \\to \\mathbf{R}$, with $f(0) = f(1) = f'(0) = 0$, which of the following is true",
        "options": [
            "$f''(x) \\neq 0$ at every point $x \\in (0, 1)$",
            "$f''(x) = 0$, for some $x \\in (0, 1)$",
            "$f''(0) = 0$",
            "$f''(x) = 0$, at every point $x \\in (0, 1)$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    182: {
        "format": "mcq",
        "body": "Let $S$ be the set of all functions $f : [0, 1] \\to R$, which are continuous on $[0, 1]$, and differentiable on $(0, 1)$. Then for every $f$ in $S$, there exists $c \\in (0, 1)$, depending on $f$, such that",
        "options": [
            "$|f(c) - f(1)| < (1 - c)|f'(c)|$",
            "$\\dfrac{f(1) - f(c)}{1 - c} = f'(c)$",
            "$|f(c) + f(1)| < (1 + c)|f'(c)|$",
            "$|f(c) - f(1)| < |f'(c)|$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    183: {
        "format": "mcq",
        "body": "Let $f$ be any function continuous on $[a, b]$ and twice differentiable on $(a, b)$. If for all $x \\in (a, b)$, $f'(x) > 0$ and $f''(x) < 0$, then for any $c \\in (a, b)$, $\\dfrac{f(c) - f(a)}{f(b) - f(c)}$ is greater than",
        "options": [
            "$\\dfrac{b + a}{b - a}$",
            "$1$",
            "$\\dfrac{b - c}{c - a}$",
            "$\\dfrac{c - a}{b - c}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
