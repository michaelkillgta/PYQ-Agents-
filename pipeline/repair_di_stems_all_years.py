#!/usr/bin/env python3
"""Restore Definite Integration stems/options from the printed papers.

Fixes empty straddle headers, JSON-escape smash (\\int/\\frac/\\text), and
paper-wrong limits. Does not touch solution_md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pyq_common as p
from agents.katex_check import katex_render_ok
from agents.publish import upsert_question
from format_ocr_math import format_ocr_math

OUT = Path(r"c:\Users\tempo\Downloads\files\out-di-yearbooks")
SMASH_INT = re.compile(r"(?<![A-Za-z\\])int(?=[_\s^{(\\])")
SMASH_FRAC = re.compile(r"(?<![A-Za-z\\])rac\{")
SMASH_TEXT = re.compile(r"(?<![A-Za-z\\])ext\{")
PLACE = re.compile(r"^(Q\d+\s*[-:]|Q\d+\s+\d{1,2}\s+January)", re.I)


def mcq(body: str, options: list[str], key: int) -> dict:
    return {
        "body": body,
        "options": options,
        "format": "mcq",
        "correct_option": key,
        "numerical_answer": None,
    }


def num(body: str, key: str) -> dict:
    return {
        "body": body,
        "options": None,
        "format": "numerical",
        "correct_option": None,
        "numerical_answer": str(key),
    }


# db q_no -> paper fields. Bodies are paper-only KaTeX.
PAPER: dict[int, dict] = {
    # --- 2023 January ---
    76: num(
        r"Let $f$ be a differentiable function defined on $\left[0,\frac{\pi}{2}\right]$ such that $f(x)>0$ and $f(x)+\int_{0}^{x} f(t)\sqrt{1-(\log_{e} f(t))^{2}}\,dt=e$, $\forall x\in\left[0,\frac{\pi}{2}\right]$. Then $6\log_{e} f\left(\frac{\pi}{6}\right)$ is equal to",
        "27",
    ),
    77: mcq(
        r"The minimum value of the function $f(x)=\int_{0}^{2} e^{|x-t|}\,dt$ is",
        [r"$2(e-1)$", r"$2e-1$", r"$2$", r"$e(e-1)$"],
        1,
    ),
    78: mcq(
        r"The value of $\displaystyle\lim_{n\to\infty}\frac{1+2-3+4+5-6+\cdots+(3n-2)+(3n-1)-3n}{\sqrt{2n^{4}+4n+3}-\sqrt{n^{4}+5n+4}}$ is :",
        [
            r"$\dfrac{\sqrt{2}+1}{2}$",
            r"$3(\sqrt{2}+1)$",
            r"$\dfrac{3}{2}(\sqrt{2}+1)$",
            r"$\dfrac{3}{2\sqrt{2}}$",
        ],
        3,
    ),
    79: mcq(
        r"The integral $16\int_{1}^{2}\dfrac{dx}{x^{3}(x^{2}+2)^{2}}$ is equal to",
        [
            r"$\dfrac{11}{6}+\log_{e} 4$",
            r"$\dfrac{11}{12}+\log_{e} 4$",
            r"$\dfrac{11}{12}-\log_{e} 4$",
            r"$\dfrac{11}{6}-\log_{e} 4$",
        ],
        4,
    ),
    80: num(
        r"If $\int_{1/3}^{3}|\log_{e} x|\,dx=\dfrac{m}{n}\log_{e}\left(\dfrac{n^{2}}{e}\right)^{m}$, where $m$ and $n$ are coprime natural numbers, then $m^{2}+n^{2}-5$ is equal to",
        "20",
    ),
    82: mcq(
        r"Let $f(x)=x+\dfrac{a}{\pi^{2}-4}\sin x+\dfrac{b}{\pi^{2}-4}\cos x$, $x\in\mathbb{R}$ be a function which satisfies $f(x)=x+\int_{0}^{\pi/2}\sin(x+y)f(y)\,dy$. Then $(a+b)$ is equal to",
        [
            r"$-\pi(\pi+2)$",
            r"$-2\pi(\pi+2)$",
            r"$-2\pi(\pi-2)$",
            r"$-\pi(\pi-2)$",
        ],
        2,
    ),
    83: mcq(
        r"The value of the integral $\int_{1/2}^{2}\dfrac{\tan^{-1}x}{x}\,dx$ is equal to",
        [
            r"$\pi\log_{e} 2$",
            r"$\dfrac{1}{2}\log_{e} 2$",
            r"$\dfrac{\pi}{4}\log_{e} 2$",
            r"$\dfrac{\pi}{2}\log_{e} 2$",
        ],
        4,
    ),
    84: mcq(
        r"The value of the integral $\int_{1}^{2}\dfrac{t^{4}+1}{t^{6}+1}\,dt$ is",
        [
            r"$\tan^{-1}\dfrac{1}{2}+\dfrac{1}{3}\tan^{-1} 8-\dfrac{\pi}{3}$",
            r"$\tan^{-1} 2-\dfrac{1}{3}\tan^{-1} 8+\dfrac{\pi}{3}$",
            r"$\tan^{-1} 2+\dfrac{1}{3}\tan^{-1} 8-\dfrac{\pi}{3}$",
            r"$\tan^{-1}\dfrac{1}{2}-\dfrac{1}{3}\tan^{-1} 8+\dfrac{\pi}{3}$",
        ],
        3,
    ),
    85: mcq(
        r"If $[t]$ denotes the greatest integer $\le t$, then the value of $\dfrac{3(e-1)^{2}}{e}\int_{1}^{e} x^{2} e^{[x]+[x^{3}]}\,dx$ is :",
        [r"$e^{9}-e$", r"$e^{8}-e$", r"$e^{7}-1$", r"$e^{8}-1$"],
        2,
    ),
    86: num(
        r"$\displaystyle\lim_{x\to 0}\dfrac{48}{x^{4}}\int_{0}^{x}\dfrac{t^{3}}{t^{6}+1}\,dt$ is equal to",
        "12",
    ),
    87: mcq(
        r"$\displaystyle\lim_{n\to\infty}\dfrac{3}{n}\left\{4+\left(2+\dfrac{1}{n}\right)^{2}+\left(2+\dfrac{2}{n}\right)^{2}+\cdots+\left(3-\dfrac{1}{n}\right)^{2}\right\}$ is equal to",
        [r"$12$", r"$\dfrac{19}{3}$", r"$0$", r"$19$"],
        4,
    ),
    88: mcq(
        r"The value of $\int_{\pi/3}^{\pi/2}\dfrac{2+3\sin x}{\sin x(1+\cos x)}\,dx$ is equal to",
        [
            r"$\dfrac{7}{2}-\sqrt{3}-\log_{e}\sqrt{3}$",
            r"$-2+3\sqrt{3}+\log_{e}\sqrt{3}$",
            r"$\dfrac{10}{3}-\sqrt{3}+\log_{e}\sqrt{3}$",
            r"$\dfrac{10}{3}-\sqrt{3}-\log_{e}\sqrt{3}$",
        ],
        3,
    ),
    89: mcq(
        r"Let a differentiable function $f$ satisfy $f(x)+\int_{3}^{x}\dfrac{f(t)}{t}\,dt=\sqrt{x+1}$, $x\ge 3$. Then $12f(8)$ is equal to:",
        ["34", "19", "17", "1"],
        3,
    ),
    91: mcq(
        r"Let $\alpha>0$. If $\int_{0}^{\alpha}\dfrac{x}{\sqrt{x+\alpha}-\sqrt{x}}\,dx=\dfrac{16+20\sqrt{2}}{15}$, then $\alpha$ is equal to :",
        ["$2$", "$4$", r"$\sqrt{2}$", r"$2\sqrt{2}$"],
        1,
    ),
    92: mcq(
        r"If $\phi(x)=\dfrac{1}{\sqrt{x}}\int_{x}^{\pi/4}(4\sqrt{2}\sin t-3\phi'(t))\,dt$, $x>0$, then $\phi'\left(\dfrac{\pi}{4}\right)$ is equal to :",
        [
            r"$\dfrac{8}{\sqrt{\pi}}$",
            r"$\dfrac{4}{6+\sqrt{\pi}}$",
            r"$\dfrac{8}{6+\sqrt{\pi}}$",
            r"$\dfrac{4}{6-\sqrt{\pi}}$",
        ],
        3,
    ),
    93: mcq(
        r"$\displaystyle\lim_{n\to\infty}\left(\dfrac{1}{1+n}+\dfrac{1}{2+n}+\dfrac{1}{3+n}+\cdots+\dfrac{1}{2n}\right)$ is equal to :",
        ["$0$", r"$\log_{e} 2$", r"$\log_{e}\left(\dfrac{3}{2}\right)$", r"$\log_{e}\left(\dfrac{2}{3}\right)$"],
        2,
    ),
    95: mcq(
        r"The value of the integral $\int_{-\pi/4}^{\pi/4}\dfrac{x+\dfrac{\pi}{4}}{2-\cos 2x}\,dx$ is",
        [
            r"$\dfrac{\pi^{2}}{6}$",
            r"$\dfrac{\pi^{2}}{12\sqrt{3}}$",
            r"$\dfrac{\pi^{2}}{3\sqrt{3}}$",
            r"$\dfrac{\pi^{2}}{6\sqrt{3}}$",
        ],
        4,
    ),
    96: num(
        r"If $\int_{0}^{\pi}\dfrac{5^{\cos x}(1+\cos x\cos 3x+\cos^{2}x+\cos^{3}x\cos 3x)}{1+5^{\cos x}}\,dx=\dfrac{k\pi}{16}$, then $k$ is equal to",
        "26",
    ),
    # --- 2024 January / February ---
    110: mcq(
        r"If $(a,b)$ be the orthocentre of the triangle whose vertices are $(1,2)$, $(2,3)$ and $(3,1)$, and $I_{1}=\int_{a}^{b} x\sin(4x-x^{2})\,dx$, $I_{2}=\int_{a}^{b}\sin(4x-x^{2})\,dx$, then $36\dfrac{I_{1}}{I_{2}}$ is equal to :",
        ["72", "88", "80", "66"],
        1,
    ),
    111: mcq(
        r"If $\int_{0}^{1}\dfrac{dx}{\sqrt{3+x}+\sqrt{1+x}}=a+b\sqrt{2}+c\sqrt{3}$, where $a,b,c$ are rational numbers, then $2a+3b-4c$ is equal to :",
        ["4", "10", "7", "8"],
        4,
    ),
    112: mcq(
        r"For $0<a<1$, the value of the integral $\int_{0}^{\pi}\dfrac{dx}{1-2a\cos x+a^{2}}$ is :",
        [
            r"$\dfrac{\pi^{2}}{\pi+a^{2}}$",
            r"$\dfrac{\pi^{2}}{\pi-a^{2}}$",
            r"$\dfrac{\pi}{1-a^{2}}$",
            r"$\dfrac{\pi}{1+a^{2}}$",
        ],
        3,
    ),
    113: num(
        r"Let $f(x)=\int_{0}^{x} g(t)\log_{e}\left(\dfrac{1-t}{1+t}\right)dt$, where $g$ is a continuous odd function. If $\int_{-\pi/2}^{\pi/2}\left(f(x)+\dfrac{x^{2}\cos x}{1+e^{x}}\right)dx=\left(\dfrac{\pi}{\alpha}\right)^{2}-\alpha$, then $\alpha$ is equal to",
        "2",
    ),
    114: mcq(
        r"If the value of the integral $\int_{-\pi/2}^{\pi/2}\left(\dfrac{x^{2}\cos x}{1+\pi^{x}}+\dfrac{1+\sin^{2}x}{1+e^{\sin x}}\right)dx=\dfrac{\pi}{4}(\pi+a)-2$, then the value of $a$ is",
        ["$3$", r"$-\dfrac{3}{2}$", "$2$", r"$\dfrac{3}{2}$"],
        1,
    ),
    115: num(
        r"If $\int_{\pi/6}^{\pi/3}\sqrt{1-\sin 2x}\,dx=\alpha+\beta\sqrt{2}+\gamma\sqrt{3}$, where $\alpha,\beta$ and $\gamma$ are rational numbers, then $3\alpha+4\beta-\gamma$ is equal to",
        "6",
    ),
    116: mcq(
        r"The value of $\displaystyle\lim_{n\to\infty}\sum_{k=1}^{n}\dfrac{n^{3}}{(n^{2}+k^{2})(n^{2}+3k^{2})}$ is:",
        [
            r"$\dfrac{(2\sqrt{3}+3)\pi}{24}$",
            r"$\dfrac{13\pi}{8(4\sqrt{3}+3)}$",
            r"$\dfrac{13(2\sqrt{3}-3)\pi}{8}$",
            r"$\dfrac{\pi}{8(2\sqrt{3}+3)}$",
        ],
        2,
    ),
    117: num(
        r"The value $9\int_{0}^{9}\left\lfloor\sqrt{\dfrac{10x}{x+1}}\right\rfloor dx$, where $\lfloor t\rfloor$ denotes the greatest integer less than or equal to $t$, is",
        "155",
    ),
    118: mcq(
        r"Let $y=f(x)$ be a thrice differentiable function in $(-5,5)$. Let the tangents to the curve $y=f(x)$ at $(1,f(1))$ and $(3,f(3))$ make angles $\dfrac{\pi}{6}$ and $\dfrac{\pi}{4}$, respectively with positive $x$-axis. If $27\int_{1}^{3}\left((f'(t))^{2}+1\right)f''(t)\,dt=\alpha+\beta\sqrt{3}$ where $\alpha,\beta$ are integers, then the value of $\alpha+\beta$ equals",
        ["$-14$", "$26$", "$-16$", "$36$"],
        2,
    ),
    119: mcq(
        r"Let $f:\mathbb{R}\to\mathbb{R}$ be defined $f(x)=ae^{2x}+be^{x}+cx$. If $f(0)=-1$, $f'(\log_{e} 2)=21$ and $\int_{0}^{\log_{e} 4}(f(x)-cx)\,dx=\dfrac{39}{2}$, then the value of $|a+b+c|$ equals:",
        ["16", "10", "12", "8"],
        4,
    ),
    120: num(
        r"If the integral $525\int_{0}^{\pi/2}\sin 2x\,\cos^{11/2}x\left(1+\cos^{5/2}x\right)^{1/2}dx$ is equal to $(n\sqrt{2}-64)$, then $n$ is equal to",
        "176",
    ),
    121: num(
        r"Let $S=(-1,\infty)$ and $f:S\to\mathbb{R}$ be defined as $f(x)=\int_{-1}^{x}(e^{t}-1)^{11}(2t-1)^{5}(t-2)^{7}(t-3)^{12}(2t-10)^{61}\,dt$. Let $p=$ sum of squares of the values of $x$ where $f(x)$ attains local maxima on $S$, and $q=$ sum of the values of $x$ where $f(x)$ attains local minima on $S$. Then the value of $p^{2}+2q$ is",
        "27",
    ),
    122: num(
        r"Let $f:\mathbb{R}\to\mathbb{R}$ be defined by $f(x)=\dfrac{4^{x}}{4^{x}+2}$ and $M=\int_{f(a)}^{f(1-a)} x\sin^{4}(x(1-x))\,dx$, $N=\int_{f(a)}^{f(1-a)}\sin^{4}(x(1-x))\,dx$; $a\neq\dfrac{1}{2}$. If $\alpha M=\beta N$, $\alpha,\beta\in\mathbb{N}$, then the least value of $\alpha^{2}+\beta^{2}$ is equal to",
        "5",
    ),
    123: mcq(
        r"Let $f,g:(0,\infty)\to\mathbb{R}$ be two functions defined by $f(x)=\int_{-x}^{x}(|t|-t^{2})e^{-t^{2}}\,dt$ and $g(x)=\int_{0}^{x^{2}} t^{1/2}e^{-t}\,dt$. Then the value of $\left(f(\sqrt{\log_{e} 9})+g(\sqrt{\log_{e} 9})\right)$ is equal to",
        ["6", "9", "8", "10"],
        3,
    ),
    124: num(
        r"$\left|\dfrac{120}{\pi^{3}}\int_{0}^{\pi}\dfrac{x^{2}\sin x\cos x}{\sin^{4}x+\cos^{4}x}\,dx\right|$ is equal to",
        "15",
    ),
    125: mcq(
        r"The value of the integral $\int_{0}^{\pi/4}\dfrac{x\,dx}{\sin^{4}(2x)+\cos^{4}(2x)}$ equals :",
        [
            r"$\dfrac{\sqrt{2}\pi^{2}}{8}$",
            r"$\dfrac{\sqrt{2}\pi^{2}}{16}$",
            r"$\dfrac{\sqrt{2}\pi^{2}}{32}$",
            r"$\dfrac{\sqrt{2}\pi^{2}}{64}$",
        ],
        3,
    ),
    126: num(
        r"If $\int_{-\pi/2}^{\pi/2}\dfrac{8\sqrt{2}\cos x\,dx}{(1+e^{\sin x})(1+\sin^{4}x)}=\alpha\pi+\beta\log_{e}(3+2\sqrt{2})$, where $\alpha,\beta$ are integers, then $\alpha^{2}+\beta^{2}$ equals",
        "8",
    ),
    128: mcq(
        r"If $\int_{0}^{\pi/3}\cos^{4}x\,dx=a\pi+b\sqrt{3}$, where $a$ and $b$ are rational numbers, then $9a+8b$ is equal to :",
        ["2", "1", "3", r"$\dfrac{3}{2}$"],
        1,
    ),
    # --- 2024 April ---
    131: num(
        r"If $\int_{0}^{\pi/4}\dfrac{\sin^{2}x}{1+\sin x\cos x}\,dx=\dfrac{1}{a}\log_{e}\left(\dfrac{a}{b}\right)+\dfrac{\pi}{b\sqrt{3}}$, where $a,b\in\mathbb{N}$, then $a+b$ is equal to",
        "8",
    ),
    132: mcq(
        r"If the value of the integral $\int_{-1}^{1}\dfrac{\cos\alpha x}{1+3^{x}}\,dx$ is $\dfrac{\pi}{2}$. Then, a value of $\alpha$ is",
        [r"$\dfrac{\pi}{3}$", r"$\dfrac{\pi}{6}$", r"$\dfrac{\pi}{4}$", r"$\dfrac{\pi}{2}$"],
        4,
    ),
    133: mcq(
        r"The value of $\int_{-\pi}^{\pi}\dfrac{2y(1+\sin y)}{1+\cos^{2}y}\,dy$ is :",
        [r"$2\pi^{2}$", r"$\dfrac{\pi^{2}}{2}$", r"$\dfrac{\pi}{2}$", r"$\pi^{2}$"],
        4,
    ),
    134: mcq(
        r"The integral $\int_{0}^{\pi/4}\dfrac{136\sin x}{3\sin x+5\cos x}\,dx$ is equal to :",
        [
            r"$3\pi-50\log_{e} 2+20\log_{e} 5$",
            r"$3\pi-25\log_{e} 2+10\log_{e} 5$",
            r"$3\pi-10\log_{e}(2\sqrt{2})+10\log_{e} 5$",
            r"$3\pi-30\log_{e} 2+20\log_{e} 5$",
        ],
        1,
    ),
    136: num(
        r"If $f(t)=\int_{0}^{\pi}\dfrac{2x\,dx}{1-\cos^{2}t\sin^{2}x}$, $0<t<\pi$, then the value of $\int_{0}^{\pi/2}\dfrac{\pi^{2}\,dt}{f(t)}$ equals",
        "1",
    ),
    137: mcq(
        r"$\int_{0}^{\pi/4}\dfrac{\cos^{2}x\sin^{2}x}{(\cos^{3}x+\sin^{3}x)^{2}}\,dx$ is equal to",
        [r"$\dfrac{1}{6}$", r"$\dfrac{1}{3}$", r"$\dfrac{1}{12}$", r"$\dfrac{1}{9}$"],
        1,
    ),
    138: num(
        r"Let $r_{k}=\dfrac{\int_{0}^{1}(1-x^{7})^{k}\,dx}{\int_{0}^{1}(1-x^{7})^{k+1}\,dx}$, $k\in\mathbb{N}$. Then the value of $\sum_{k=1}^{10}\dfrac{1}{7(r_{k}-1)}$ is equal to",
        "65",
    ),
    139: num(
        r"Let $[t]$ denote the largest integer less than or equal to $t$. If $\int_{0}^{3}\left([x^{2}]+\left[\dfrac{x^{2}}{2}\right]\right)dx=a+b\sqrt{2}-\sqrt{3}-\sqrt{5}+c\sqrt{6}-\sqrt{7}$, where $a,b,c\in\mathbb{Z}$, then $a+b+c$ is equal to",
        "23",
    ),
    140: mcq(
        r"The value of $k\in\mathbb{N}$ for which the integral $I_{n}=\int_{0}^{1}(1-x^{k})^{n}\,dx$, $n\in\mathbb{N}$, satisfies $147I_{20}=148I_{21}$ is",
        ["14", "8", "10", "7"],
        4,
    ),
    141: mcq(
        r"Let $\int_{\alpha}^{\log_{e} 4}\dfrac{dx}{\sqrt{e^{x}-1}}=\dfrac{\pi}{6}$. Then $e^{\alpha}$ and $e^{-\alpha}$ are the roots of the equation :",
        [
            r"$x^{2}+2x-8=0$",
            r"$x^{2}-2x-8=0$",
            r"$2x^{2}-5x+2=0$",
            r"$2x^{2}-5x-2=0$",
        ],
        3,
    ),
    142: mcq(
        r"Let $\int_{0}^{x}\sqrt{1-(y'(t))^{2}}\,dt=\int_{0}^{x} y(t)\,dt$, $0\le x\le 3$, $y\ge 0$, $y(0)=0$. Then at $x=2$, $y''+y+1$ is equal to",
        ["$1$", "$2$", r"$\sqrt{2}$", r"$\dfrac{1}{2}$"],
        1,
    ),
    143: mcq(
        r"The value of the integral $\int_{-1}^{2}\log_{e}\left(x+\sqrt{x^{2}+1}\right)dx$ is",
        [
            r"$\sqrt{5}-\sqrt{2}+\log_{e}\left(\dfrac{7+4\sqrt{5}}{1+\sqrt{2}}\right)$",
            r"$\sqrt{5}-\sqrt{2}+\log_{e}\left(\dfrac{9+4\sqrt{5}}{1+\sqrt{2}}\right)$",
            r"$\sqrt{2}-\sqrt{5}+\log_{e}\left(\dfrac{7+4\sqrt{5}}{1+\sqrt{2}}\right)$",
            r"$\sqrt{2}-\sqrt{5}+\log_{e}\left(\dfrac{9+4\sqrt{5}}{1+\sqrt{2}}\right)$",
        ],
        4,
    ),
    6: mcq(
        r"The value of $\alpha$ for which $4\alpha\int_{-1}^{2} e^{-\alpha|x|}\,dx=5$, is:",
        [r"$\ln 2$", r"$\ln\sqrt{2}$", r"$\ln\dfrac{3}{4}$", r"$\ln\dfrac{4}{3}$"],
        1,
    ),
    9: mcq(
        r"Find the value of $\int_{0}^{2\pi}\dfrac{x\sin^{8}x}{\sin^{8}x+\cos^{8}x}\,dx$",
        [r"$\pi^{2}$", r"$2\pi^{2}$", r"$3\pi^{2}$", r"$4\pi^{2}$"],
        1,
    ),
    33: num(
        r"Let $f(\theta)=\sin\theta+\int_{-\pi/2}^{\pi/2}(\sin\theta+t\cos\theta)f(t)\,dt$. Then the value of $\int_{0}^{\pi/2}f(\theta)\,d\theta$ is",
        "1",
    ),
    42: num(
        r"The value of the integral $\dfrac{48}{\pi^{4}}\int_{0}^{\pi}\left(\dfrac{3\pi x^{2}}{2}-x^{3}\right)\dfrac{\sin x}{1+\cos^{2}x}\,dx$ is equal to",
        "6",
    ),
    107: mcq(
        r"The value of $\dfrac{e^{-\pi/4}+\int_{0}^{\pi/4}e^{-x}\tan^{50}x\,dx}{\int_{0}^{\pi/4}e^{-x}(\tan^{49}x+\tan^{51}x)\,dx}$ is",
        ["51", "50", "25", "49"],
        2,
    ),
    32: mcq(
        r"Let $g(x)=\int_{0}^{x} f(t)\,dt$, where $f$ is a continuous function on $[0,3]$ such that $\dfrac{1}{3}\le f(t)\le 1$ for all $t\in[0,1]$ and $0\le f(t)\le\dfrac{1}{2}$ for all $t\in(1,3]$. The largest possible interval in which $g(3)$ lies is:",
        [
            r"$\left[-1,-\dfrac{1}{2}\right]$",
            r"$\left[-\dfrac{3}{2},-1\right]$",
            r"$\left[\dfrac{1}{3},2\right]$",
            r"$[1,3]$",
        ],
        3,
    ),
    154: mcq(
        r"If $I=\int_{0}^{\pi/2}\dfrac{\sin^{2}x}{\sin^{3}x+\cos^{3}x}\,dx$, then $\int_{0}^{\pi/2}\dfrac{x\sin x\cos x}{\sin^{4}x+\cos^{4}x}\,dx$ equals :",
        [r"$\dfrac{\pi^{2}}{12}$", r"$\dfrac{\pi^{2}}{4}$", r"$\dfrac{\pi^{2}}{16}$", r"$\dfrac{\pi^{2}}{8}$"],
        3,
    ),
    181: mcq(
        r"If $f'(x)=\tan^{-1}(\sec x+\tan x)$, $x\in\left(-\dfrac{\pi}{2},\dfrac{\pi}{2}\right)$ and $f(0)=0$ then the value of $f(1)$ is",
        [r"$\dfrac{\pi+1}{4}$", r"$\dfrac{\pi-1}{4}$", r"$\dfrac{\pi+1}{2}$", r"$0$"],
        1,
    ),
    182: num(
        r"The integral $\int_{0}^{2}\big||x-1|-x\big|\,dx$ is equal to",
        "1.5",
    ),
    183: num(
        r"Let $[t]$ denote the greatest integer less than or equal to $t$. Then the value of $\int_{1}^{2}|2x-[3x]|\,dx$ is",
        "1",
    ),
    188: num(
        r"Let $\{x\}$ and $[x]$ denote the fractional part of $x$ and the greatest integer $\le x$ respectively of a real number $x$. If $\int_{0}^{n}\{x\}\,dx$, $\int_{0}^{n}[x]\,dx$ and $10(n^{2}-n)$, $(n\in\mathbb{N}, n>1)$ are three consecutive terms of a G.P., then $n$ is equal to",
        "21",
    ),
    62: mcq(
        r"Let $f(x)=2+|x|-|x-1|+|x+1|$, $x\in\mathbb{R}$. Consider (S1) : $f'\left(-\dfrac{3}{2}\right)+f'\left(-\dfrac{1}{2}\right)+f'\left(\dfrac{1}{2}\right)+f'\left(\dfrac{3}{2}\right)=2$. (S2) : $\int_{-2}^{2} f(x)\,dx=12$. Then,",
        [
            "both (S1) and (S2) are correct",
            "both (S1) and (S2) are wrong",
            "only (S1) is correct",
            "only (S2) is correct",
        ],
        4,
    ),
    190: mcq(
        r"If $I_{1}=\int_{0}^{1}(1-x^{50})^{100}\,dx$ and $I_{2}=\int_{0}^{1}(1-x^{50})^{101}\,dx$ such that $I_{2}=\alpha I_{1}$ then $\alpha$ equals to :",
        [
            r"$\dfrac{5051}{5050}$",
            r"$\dfrac{5050}{5050}$",
            r"$\dfrac{5051}{5049}$",
            r"$\dfrac{5049}{5050}$",
        ],
        2,
    ),
}


def unsSmash(s: str) -> str:
    s = (s or "").replace("\x0c", "").replace("∪", r"\int").replace("∫", r"\int")
    s = SMASH_FRAC.sub(r"\\frac{", s)
    s = SMASH_TEXT.sub(r"\\text{", s)
    s = SMASH_INT.sub(r"\\int", s)
    return s


def flags_of(body: str, options: list[str] | None) -> list[str]:
    blob = body + "\n" + "\n".join(options or [])
    flags = []
    if PLACE.search((body or "").strip()) or len((body or "").strip()) < 40:
        flags.append("placeholder")
    if SMASH_INT.search(blob):
        flags.append("int")
    if SMASH_FRAC.search(blob):
        flags.append("rac")
    if SMASH_TEXT.search(blob):
        flags.append("ext")
    if "∪" in blob or "U_0^" in blob:
        flags.append("cup")
    return flags


def apply_row(sb, row: dict, entry: dict) -> None:
    body = format_ocr_math(entry["body"])
    options = entry.get("options")
    if isinstance(options, list):
        options = [format_ocr_math(o) for o in options]
    spec = {
        "answer_type": entry["format"],
        "answer_value": (
            str(entry["correct_option"])
            if entry["format"] == "mcq"
            else str(entry["numerical_answer"])
        ),
    }
    fields = [body] + (options or [])
    if not all(katex_render_ok(t) for t in fields):
        raise SystemExit(f"KaTeX fail Q{row['q_no']}: {body[:120]}")
    payload = {"body": body, "options": options}
    upsert_question(
        sb,
        row["id"],
        payload,
        row["review_status"],
        float(row.get("extraction_confidence") or 1.0),
        spec,
        answer=spec["answer_value"],
    )
    patch = {
        "format": entry["format"],
        "correct_option": entry["correct_option"],
        "numerical_answer": entry["numerical_answer"],
    }
    sb.table("pyq_questions").update(patch).eq("id", row["id"]).execute()
    if entry["format"] == "numerical":
        sb.table("pyq_question_options").delete().eq("question_id", row["id"]).execute()


def main() -> int:
    p.configure_book("math")
    sb = p.supabase_client()
    cid = p.resolve_chapter_id(sb, 17, "Mathematics")
    rows = (
        sb.table("pyq_questions")
        .select(
            "id,q_no,exam_date,exam_shift,format,body,correct_option,numerical_answer,"
            "review_status,extraction_confidence,"
            "question_options:pyq_question_options(option_index,body)"
        )
        .eq("chapter_id", cid)
        .in_("review_status", ["auto_ok", "human_ok"])
        .order("q_no")
        .execute()
        .data
        or []
    )
    changed: list[int] = []
    for row in rows:
        qn = int(row["q_no"])
        if qn in PAPER:
            apply_row(sb, row, PAPER[qn])
            changed.append(qn)
            print(f"paper Q{qn}", flush=True)
            continue
        body = unsSmash(row.get("body") or "")
        opts_raw = sorted(row.get("question_options") or [], key=lambda o: o.get("option_index") or 0)
        opts = [unsSmash(o.get("body") or "") for o in opts_raw]
        if body == (row.get("body") or "") and all(
            opts[i] == (opts_raw[i].get("body") or "") for i in range(len(opts))
        ):
            continue
        fmt = row.get("format") or "mcq"
        entry = {
            "body": body,
            "options": opts if fmt == "mcq" and len(opts) == 4 else None,
            "format": fmt,
            "correct_option": row.get("correct_option"),
            "numerical_answer": row.get("numerical_answer"),
        }
        apply_row(sb, row, entry)
        changed.append(qn)
        print(f"unsSmash Q{qn}", flush=True)

    # re-fetch verifier
    rows = (
        sb.table("pyq_questions")
        .select(
            "q_no,exam_date,format,body,"
            "question_options:pyq_question_options(option_index,body)"
        )
        .eq("chapter_id", cid)
        .in_("review_status", ["auto_ok", "human_ok"])
        .order("exam_date")
        .order("q_no")
        .execute()
        .data
        or []
    )
    bad = []
    by_year: dict[str, int] = {}
    for row in rows:
        y = str(row.get("exam_date") or "")[:4]
        by_year[y] = by_year.get(y, 0) + 1
        opts = [
            o.get("body") or ""
            for o in sorted(row.get("question_options") or [], key=lambda o: o.get("option_index") or 0)
        ]
        body = row.get("body") or ""
        fl = flags_of(body, opts)
        katex_ok = all(katex_render_ok(t) for t in [body] + opts)
        if fl or not katex_ok:
            bad.append({"q_no": row["q_no"], "date": row.get("exam_date"), "flags": fl, "katex": katex_ok, "preview": body[:140]})
    dump = {"changed": changed, "counts": by_year, "bad": bad}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stem_repair_verify.json").write_text(json.dumps(dump, indent=2), encoding="utf-8")
    print(f"changed {len(changed)} live {sum(by_year.values())} remaining_flags {len(bad)}", flush=True)
    for b in bad:
        print(f"  BAD Q{b['q_no']} {b['date']} katex={b['katex']} {b['flags']} {b['preview']!r}", flush=True)
    return 0 if not bad else 2


if __name__ == "__main__":
    sys.exit(main())
