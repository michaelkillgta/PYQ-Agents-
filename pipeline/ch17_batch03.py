#!/usr/bin/env python3
"""AoD ch17 held batch 3: Q17,43,48-51."""
from ch17_push import push_repairs

REPAIRS = {
    17: {
        "format": "mcq",
        "body": "If the function $f(x) = 2x^{3} - 9ax^{2} + 12a^{2}x + 1$, where $a > 0$, attains its local maximum and local minimum values at $p$ and $q$, respectively, such that $p^{2} = q$, then $f(3)$ is equal to",
        "options": ["$55$", "$10$", "$23$", "$37$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    43: {
        "format": "numerical",
        "body": "Let $M$ and $N$ be the number of points on the curve $y^{5} - 9xy + 2x = 0$, where the tangents to the curve are parallel to $x$-axis and $y$-axis, respectively. Then the value of $M + N$ equals _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    48: {
        "format": "mcq",
        "body": "If the tangent to the curve $y = x^{3}$ at the point $P(t, t^{3})$ meets the curve again at $Q$, then the ordinate of the point which divides $PQ$ internally in the ratio $1 : 2$ is",
        "options": ["$0$", "$-2t^{3}$", "$-t^{3}$", "$2t^{3}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    49: {
        "format": "numerical",
        "body": "If the area of the triangle formed by the $x$-axis, the normal and the tangent to the circle $(x - 2)^{2} + (y - 3)^{2} = 25$ at the point $(5, 7)$ is $A$, then $24A$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "1225",
    },
    50: {
        "format": "numerical",
        "body": "If the curves $x = y^{4}$ and $xy = k$ cut at right angles, then $(4k)^{6}$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    51: {
        "format": "mcq",
        "body": "Let $P(h, k)$ be a point on the curve $y = x^{2} + 7x + 2$, nearest to the line, $y = 3x - 3$. Then the equation of the normal to the curve at $P$ is",
        "options": [
            "$x + 3y + 26 = 0$",
            "$x + 3y - 62 = 0$",
            "$x - 3y - 11 = 0$",
            "$x - 3y + 22 = 0$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
