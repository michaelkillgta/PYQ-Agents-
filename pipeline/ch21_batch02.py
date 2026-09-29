#!/usr/bin/env python3
"""DE ch21 batch 2: Q12,14,15,17,24,32."""
from ch21_push import push_repairs

REPAIRS = {
    12: {
        "format": "mcq",
        "body": "If $\\dfrac{dy}{dx} = \\dfrac{xy}{x^{2} + y^{2}}$; $y(1) = 1$; then a value of $x$ satisfying $y(x) = e$ is",
        "options": [
            "$\\dfrac{1}{2}\\sqrt{3e}$",
            "$\\dfrac{e}{\\sqrt{2}}$",
            "$\\sqrt{2e}$",
            "$\\sqrt{3e}$",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    14: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $2\\cos x\\,\\dfrac{dy}{dx} = \\sin 2x - 4y\\sin x$, $x \\in \\left(0, \\dfrac{\\pi}{2}\\right)$. If $y\\left(\\dfrac{\\pi}{3}\\right) = 0$, then $y'\\left(\\dfrac{\\pi}{4}\\right) + y\\left(\\dfrac{\\pi}{4}\\right)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "1",
    },
    15: {
        "format": "numerical",
        "body": "Let the solution $y = y(x)$ of the differential equation $\\dfrac{dy}{dx} - y = 1 + 4\\sin x$ satisfy $y(\\pi) = 1$. Then $y\\left(\\dfrac{\\pi}{2}\\right) + 10$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "7",
    },
    17: {
        "format": "mcq",
        "body": "Let $y = y(t)$ be a solution of the differential equation $\\dfrac{dy}{dt} + \\alpha y = \\gamma e^{-\\beta t}$, where $\\alpha > 0$, $\\beta > 0$ and $\\gamma > 0$. Then $\\lim_{t \\to \\infty} y(t)$",
        "options": ["is $0$", "does not exist", "is $1$", "is $-1$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    24: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\cos x\\,\\dfrac{dy}{dx} + 2y\\sin x = \\sin 2x$, $x \\in \\left(0, \\dfrac{\\pi}{2}\\right)$. If $y(\\pi/3) = 0$, then $y(\\pi/4)$ is equal to",
        "options": ["$2 - \\sqrt{2}$", "$2 + \\sqrt{2}$", "$\\sqrt{2} - 2$", "$\\dfrac{1}{\\sqrt{2}} - 1$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    32: {
        "format": "mcq",
        "body": "A differential equation representing the family of parabolas with axis parallel to $y$-axis and whose length of latus rectum is the distance of the point $(2, -3)$ from the line $3x + 4y = 5$, is given by which of the following",
        "options": [
            "$11\\dfrac{d^{2}x}{dy^{2}} = 10$",
            "$11\\dfrac{d^{2}y}{dx^{2}} = 10$",
            "$10\\dfrac{d^{2}y}{dx^{2}} = 11$",
            "$10\\dfrac{d^{2}x}{dy^{2}} = 11$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
