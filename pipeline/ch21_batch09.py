#!/usr/bin/env python3
"""DE ch21 batch 9: Q171,172,176,180,182,190."""
from ch21_push import push_repairs

REPAIRS = {
    171: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $(1 + x^{2})\\dfrac{dy}{dx} + y = e^{\\tan^{-1} x}$, $y(1) = 0$. Then $y(0)$ is",
        "options": [
            "$\\dfrac{1}{2}(e^{\\pi/2} - 1)$",
            "$\\dfrac{1}{2}(1 - e^{\\pi/2})$",
            "$\\dfrac{1}{4}(1 - e^{\\pi/2})$",
            "$\\dfrac{1}{4}(e^{\\pi/2} - 1)$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    172: {
        "format": "mcq",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} = \\dfrac{(\\tan x) + y}{\\sin x(\\sec x - \\sin x\\tan x)}$, $x \\in (0, \\pi/2)$ satisfying the condition $y(\\pi/4) = 2$. Then $y(\\pi/3)$ is",
        "options": [
            "$\\sqrt{3}(2 + \\log_{e}\\sqrt{3})$",
            "$\\dfrac{\\sqrt{3}}{2}(2 + \\log_{e} 3)$",
            "$\\sqrt{3}(1 + 2\\log_{e} 3)$",
            "$\\sqrt{3}(2 + \\log_{e} 3)$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    176: {
        "format": "numerical",
        "body": "Let $f : \\mathbb{R} \\to \\mathbb{R}$ be a differentiable function such that $f'(x) + f(x) = \\int_{0}^{2} f(t)\\,dt$. If $f(0) = e^{-2}$, then $2f(0) - f(2)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "1",
    },
    180: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be the solution of the differential equation $\\dfrac{dy}{dx} + \\dfrac{\\sqrt{2} y}{2\\cos^{4} x - \\cos 2x} = x e^{\\tan^{-1}(\\sqrt{2}\\cot 2x)}$, $0 < x < \\pi/2$ with $y(\\pi/4) = \\pi^{2}/32$. If $y(\\pi/3) = \\dfrac{\\pi^{2}}{18} e^{-\\tan^{-1}(\\alpha)}$, then the value of $3\\alpha^{2}$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    182: {
        "format": "numerical",
        "body": "Let $y = y(x)$ be solution of the following differential equation $e^{y}\\dfrac{dy}{dx} - 2e^{y}\\sin x + \\sin x\\cos^{2} x = 0$, $y(\\pi/2) = 0$. If $y(0) = \\log_{e}(\\alpha + \\beta e^{-2})$, then $4(\\alpha + \\beta)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    190: {
        "format": "numerical",
        "body": "Let $\\alpha |x| = |y| e^{xy - \\beta}$, $\\alpha, \\beta \\in \\mathbb{N}$ be the solution of the differential equation $x\\,dy - y\\,dx + xy(x\\,dy + y\\,dx) = 0$, $y(1) = 2$. Then $\\alpha + \\beta$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
}

if __name__ == "__main__":
    push_repairs(REPAIRS)
