#!/usr/bin/env python3
"""DE ch21 leftover smash: Q23,26,27,28,30,45."""
from ch21_push import push_repairs

REPAIRS = {
    23: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation $\\dfrac{dy}{dx} + (\\tan x)y = \\sin x$, $0 \\le x \\le \\dfrac{\\pi}{3}$, with $y(0) = 0$, then $y\\left(\\dfrac{\\pi}{4}\\right)$ is equal to",
        "options": [
            "$\\dfrac{1}{4}\\log_{e} 2$",
            "$\\left(\\dfrac{1}{2\\sqrt{2}}\\right)\\log_{e} 2$",
            "$\\log_{e} 2$",
            "$\\dfrac{1}{2}\\log_{e} 2$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    26: {
        "format": "mcq",
        "body": "If $y = y(x)$ is the solution of the differential equation, $x\\dfrac{dy}{dx} + 2y = x^{2}$ satisfying $y(1) = 1$, then $y\\left(\\dfrac{1}{2}\\right)$ is equal to",
        "options": ["$\\dfrac{7}{64}$", "$\\dfrac{1}{4}$", "$\\dfrac{13}{16}$", "$\\dfrac{49}{16}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    27: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation, $x\\dfrac{dy}{dx} + y = x\\log_{e} x$, $(x > 1)$. If $2y(2) = \\log_{e} 4 - 1$, then $y(e)$ is equal to",
        "options": ["$-\\dfrac{e}{2}$", "$\\dfrac{e}{4}$", "$-\\dfrac{e^{2}}{2}$", "$\\dfrac{e^{2}}{4}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    28: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $x\\,dy = (y + x^{3}\\cos x)\\,dx$ with $y(\\pi) = 0$, then $y\\left(\\dfrac{\\pi}{2}\\right)$ is equal to",
        "options": [
            "$\\dfrac{\\pi^{2}}{4} + \\dfrac{\\pi}{2}$",
            "$\\dfrac{\\pi^{2}}{2} + \\dfrac{\\pi}{4}$",
            "$\\dfrac{\\pi^{2}}{2} - \\dfrac{\\pi}{4}$",
            "$\\dfrac{\\pi^{2}}{4} - \\dfrac{\\pi}{2}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    30: {
        "format": "mcq",
        "body": "The population $P = P(t)$ at time $t$ of a certain species follows the differential equation $\\dfrac{dP}{dt} = 0.5P - 450$. If $P(0) = 850$, then the time at which population becomes zero is",
        "options": [
            "$\\log_{e} 9$",
            "$2\\log_{e} 18$",
            "$\\log_{e} 18$",
            "$\\dfrac{1}{2}\\log_{e} 18$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    45: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $e^{x}\\sqrt{1 - y^{2}}\\,dx + \\left(\\dfrac{y}{x}\\right)dy = 0$, $y(1) = -1$. Then the value of $(y(3))^{2}$ is equal to",
        "options": ["$1 - 4e^{3}$", "$1 - 4e^{6}$", "$1 + 4e^{3}$", "$1 + 4e^{6}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
