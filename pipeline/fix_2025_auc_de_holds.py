#!/usr/bin/env python3
"""Promote the five 2025 AUC/DE holds after KaTeX repairs."""
from __future__ import annotations

import pyq_common as p
from agents.katex_check import katex_render_ok

FIXES = {
    211: r"The area (in sq. units) of the region $\{(x, y) : 0 \le y \le 2|x|+1,\ 0 \le y \le x^{2}+1,\ |x| \le 3\}$ is",
    192: r"The area of the region $\{(x, y) : |x-y| \le y \le 4\sqrt{x}\}$ is",
    197: r"If the area of the region $\{(x, y) : 1 + x^{2} \le y \le \min\{x+7,\ 11-3x\}\}$ is $A$, then $3A$ is equal to",
    203: (
        r"If a curve $y=y(x)$ passes through the point $\left(1, \frac{\pi}{2}\right)$ "
        r"and satisfies the differential equation "
        r"$(7x^{4} \cot y - e^{x} \csc y)\dfrac{dx}{dy} = x^{5},\ x \ge 1$, "
        r"then at $x=2$, the value of $\cos y$ is:"
    ),
    207: (
        r"Let $y=y(x)$ be the solution curve of the differential equation "
        r"$x(x^{2}+e^{x})\,dy+(e^{x}(x-2)y-x^{3})\,dx=0,\ x>0$ "
        r"passing through the point $(1,0)$. Then $y(2)$ is equal to :"
    ),
}


def main() -> int:
    sb = p.supabase_client()
    cid = p.resolve_chapter_id(sb, 17, "Mathematics")
    for q_no, body in FIXES.items():
        ok = katex_render_ok(body)
        print(f"q{q_no} katex={ok}", flush=True)
        if not ok:
            return 2
        sb.table("pyq_questions").update({
            "body": body,
            "review_status": "human_ok",
            "extraction_confidence": 1.0,
        }).eq("chapter_id", cid).eq("q_no", q_no).execute()
        print(f"  promoted q_no {q_no}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
