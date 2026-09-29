#!/usr/bin/env python3
"""Fix Q21 fill-gate truncated-tail."""
from ch17_push import push_repairs

REPAIRS = {
    21: {
        "format": "mcq",
        "body": "The function $f(x) = 2x + 3x^{\\frac{2}{3}}$, $x \\in R$, has which of the following",
        "options": [
            "exactly one point of local minima and no point of local maxima",
            "exactly one point of local maxima and no point of local minima",
            "exactly one point of local maxima and exactly one point of local minima",
            "exactly two points of local maxima and exactly one point of local minima",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
