#!/usr/bin/env python3
"""Replace smashed Document-AI stems with paper-faithful KaTeX from the 2026 Jan PDF.

glm5.3-flash read the printed page; Document AI + gemma4 did not. Scoring still
uses the PDF answer key.
"""
from __future__ import annotations

import json
from pathlib import Path

import pyq_common as p
from agents.katex_check import katex_render_ok
from agents.publish import upsert_question
from audit_paper_text import flags_for
from ingest_math_2026_jan_definite import (
    BRAND,
    CHAPTER_ID,
    JEE_SESSION,
    PDF_KEY,
    Q_NO_OFFSET,
    strip_branding,
)

OUT = Path(r"c:\Users\tempo\Downloads\files\out-math-2026-jan-di")

# Printed paper (pages 1–2) + answer-key page. Overlay branding omitted.
PAPER = {
    1: {
        "body": r"If $\int_{0}^{1} 4\cot^{-1}(1-2x+4x^{2})\,dx = a\tan^{-1}(2)-b\log_{e}(5)$, where $a,b\in\mathbb{N}$, then $(2a+b)$ is equal to",
        "options": None,
    },
    2: {
        "body": r"The value of the integral $\displaystyle\int_{\pi/24}^{5\pi/24}\dfrac{dx}{1+\sqrt[3]{\tan 2x}}$ is :",
        "options": [r"$\pi/3$", r"$\pi/12$", r"$\pi/18$", r"$\pi/6$"],
    },
    3: {
        "body": r"Let $[\cdot]$ denote the greatest integer function. Then $\displaystyle\int_{-\pi/2}^{\pi/2}\dfrac{12(3+[x])}{3+[\sin x]+[\cos x]}\,dx$ is equal to :",
        "options": [r"$13\pi+1$", r"$12\pi+5$", r"$11\pi+2$", r"$15\pi+4$"],
    },
    4: {
        "body": r"If $f(x)$ satisfies the relation $f(x)=e^{x}+\int_{0}^{1}(y+xe^{x})f(y)\,dy$, then $e+f(0)$ is equal to",
        "options": None,
    },
    5: {
        "body": r"Let $f(x)=[x]^{2}-[x+3]-3$, $x\in\mathbb{R}$, where $[\cdot]$ is the greatest integer function. Then",
        "options": [
            r"$\int_{0}^{2}f(x)\,dx=-6$",
            r"$f(x)<0$ only for $x\in[-1,3)$",
            r"$f(x)>0$ only for $x\in[4,\infty)$",
            r"$f(x)=0$ for finitely many values of $x$",
        ],
    },
    6: {
        "body": r"Let $[\cdot]$ be the greatest integer function. If $\alpha=\int_{0}^{64}(x^{1/3}-[x^{1/3}])\,dx$, then $\dfrac{1}{\pi}\int_{0}^{\alpha\pi}\dfrac{\sin^{2}\theta}{\sin^{6}\theta+\cos^{6}\theta}\,d\theta$ is equal to",
        "options": None,
    },
    7: {
        "body": r"The value of $\displaystyle\int_{-\pi/2}^{\pi/2}\dfrac{1}{[x]+4}\,dx$, where $[\cdot]$ denotes the greatest integer function, is",
        "options": [
            r"$\dfrac{1}{60}(21\pi-1)$",
            r"$\dfrac{7}{60}(\pi-3)$",
            r"$\dfrac{7}{60}(3\pi-1)$",
            r"$\dfrac{1}{60}(\pi-7)$",
        ],
    },
    8: {
        "body": r"The number of elements in the set $S$ of all $x\in[0,100]$ such that $\int_{0}^{x}t^{2}\sin(x-t)\,dt=x^{2}$ is",
        "options": None,
    },
    9: {
        "body": r"The value of $\displaystyle\int_{-\pi/6}^{\pi/6}\dfrac{\pi+4x^{11}}{1-\sin(|x|+\pi/6)}\,dx$ is equal to:",
        "options": [r"$8\pi$", r"$6\pi$", r"$2\pi$", r"$4\pi$"],
    },
    10: {
        "body": r"$6\int_{0}^{\pi}|\sin 3x+\sin 2x+\sin x|\,dx$ is equal to",
        "options": None,
    },
    11: {
        "body": r"Let $f$ be a polynomial function such that $f(x^{2}+1)=x^{4}+5x^{2}+2$, for all $x\in\mathbb{R}$. Then $\int_{0}^{3}f(x)\,dx$ is equal to",
        "options": [r"$\dfrac{5}{3}$", r"$\dfrac{41}{3}$", r"$\dfrac{27}{2}$", r"$\dfrac{33}{2}$"],
    },
    12: {
        "body": r"If $\displaystyle\int\dfrac{1-5\cos^{2}x}{\sin^{5}x\cos^{2}x}\,dx=f(x)+C$, where $C$ is the constant of integration, then $f(\pi/6)-f(\pi/4)$ is equal to",
        "options": [
            r"$\dfrac{1}{\sqrt{3}}(26+\sqrt{3})$",
            r"$\dfrac{1}{\sqrt{3}}(26-\sqrt{3})$",
            r"$\dfrac{4}{\sqrt{3}}(8-\sqrt{6})$",
            r"$\dfrac{2}{\sqrt{3}}(4+\sqrt{6})$",
        ],
    },
    13: {
        "body": r"The value of $\displaystyle\sum_{r=1}^{20}\left(\sqrt{\pi}\left(\int_{0}^{r}x|\sin\pi x|\,dx\right)\right)$ is",
        "options": None,
    },
    14: {
        "body": r"Let a differentiable function $f$ satisfy the equation $\int_{0}^{36}f\left(\dfrac{tx}{36}\right)\,dt=4\alpha f(x)$. If $y=f(x)$ is a standard parabola passing through the points $(2,1)$ and $(-4,\beta)$, then $\beta\alpha$ is equal to",
        "options": None,
    },
}


def main() -> int:
    parsed = {}
    failed = []
    for q_no, rec in PAPER.items():
        body = strip_branding(rec["body"])
        options = rec["options"]
        if options:
            options = [strip_branding(o) for o in options]
        fields = [body, *(options or [])]
        for t in fields:
            if JEE_SESSION.search(t) or BRAND.search(t):
                failed.append((q_no, "branding", t[:80]))
            hits = flags_for(t, is_option=t in (options or []))
            if hits:
                failed.append((q_no, hits, t[:80]))
            if not katex_render_ok(t):
                failed.append((q_no, "katex", t[:120]))
        kind, _val = PDF_KEY[q_no]
        parsed[str(q_no)] = {
            "body": body,
            "options": options if kind == "mcq" else None,
            "page": 1 if q_no <= 8 else 2,
        }
    out = OUT / "agents" / "parsed_paper.json"
    out.write_text(json.dumps(parsed, ensure_ascii=False, indent=1), encoding="utf-8")
    if failed:
        print("failed checks:")
        for row in failed:
            print(" ", row)
        return 2

    sb = p.supabase_client()
    rows = (
        sb.table("pyq_questions")
        .select("id,q_no")
        .eq("chapter_id", CHAPTER_ID)
        .gte("q_no", Q_NO_OFFSET + 1)
        .lte("q_no", Q_NO_OFFSET + 14)
        .execute()
        .data
    )
    ids = {int(r["q_no"]) - Q_NO_OFFSET: r["id"] for r in rows}
    for q_no, entry in parsed.items():
        n = int(q_no)
        kind, val = PDF_KEY[n]
        spec = {"answer_type": kind, "answer_value": val}
        upsert_question(sb, ids[n], entry, "human_ok", 1.0, spec, answer=val)
        print(f"Q{n} paper human_ok", flush=True)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
