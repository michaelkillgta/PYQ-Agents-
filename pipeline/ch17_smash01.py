#!/usr/bin/env python3
"""AoD ch17 smash leftover: Q2,36,133-135,139,158."""
from ch17_push import push_repairs

REPAIRS = {
    2: {
        "format": "mcq",
        "body": "A spherical iron ball of $10$ cm radius is coated with a layer of ice of uniform thickness that melts at a rate of $50$ cm$^{3}$/min. When the thickness of ice is $5$ cm, then the rate (in cm/min) at which the thickness of ice decreases, is",
        "options": [
            "$\\dfrac{5}{6\\pi}$",
            "$\\dfrac{1}{54\\pi}$",
            "$\\dfrac{1}{36\\pi}$",
            "$\\dfrac{1}{18\\pi}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    36: {
        "format": "mcq",
        "body": "If the surface area of a cube is increasing at a rate of $3.6$ cm$^{2}$/sec, retaining its shape, then the rate of change of its volume (in cm$^{3}$/sec), when the length of a side of the cube is $10$ cm, is",
        "options": ["$20$", "$10$", "$18$", "$9$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    133: {
        "format": "mcq",
        "body": "If $m$ is the minimum value of $k$ for which the function $f(x) = x\\sqrt{kx - x^{2}}$ is increasing in the interval $[0, 3]$ and $M$ is the maximum value of $f$ in $[0, 3]$ when $k = m$, then the ordered pair $(m, M)$ is equal to",
        "options": [
            "$(4, 3\\sqrt{3})$",
            "$(5, 3\\sqrt{6})$",
            "$(3, 3\\sqrt{3})$",
            "$(4, 3\\sqrt{2})$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    134: {
        "format": "mcq",
        "body": "The maximum volume (in cu. m) of the right circular cone having slant height $3$ m is",
        "options": ["$2\\sqrt{3}\\,\\pi$", "$3\\sqrt{3}\\,\\pi$", "$6\\pi$", "$\\dfrac{4}{3}\\pi$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    135: {
        "format": "mcq",
        "body": "The maximum area (in sq. units) of a rectangle having its base on the $x$-axis and its other two vertices on the parabola $y = 12 - x^{2}$ such that the rectangle lies inside the parabola, is",
        "options": ["$20\\sqrt{2}$", "$32$", "$36$", "$18\\sqrt{3}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    139: {
        "format": "mcq",
        "body": "If $c$ is a point at which Rolle's theorem holds for the function $f(x) = \\log_{e}\\left(\\dfrac{x^{2} + \\alpha}{7x}\\right)$ in the interval $[3, 4]$, where $\\alpha \\in R$, then $f''(c)$ is equal to",
        "options": ["$-\\dfrac{1}{12}$", "$\\dfrac{1}{12}$", "$-\\dfrac{1}{24}$", "$\\dfrac{\\sqrt{3}}{7}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    158: {
        "format": "mcq",
        "body": "If the function $f$ given by $f(x) = x^{3} - 3(a - 2)x^{2} + 3ax + 7$, for some $a \\in R$ is increasing in $(0, 1]$ and decreasing in $[1, 5)$, then a root of the equation $\\dfrac{f(x) - 14}{(x - 1)^{2}} = 0$, $(x \\neq 1)$ is",
        "options": ["$7$", "$-7$", "$6$", "$5$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
