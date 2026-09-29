#!/usr/bin/env python3
"""Move page-straddle stems onto the printed Q numbers."""
from __future__ import annotations

import json
import sys

import pyq_common as p
from finish_di_remaining import fetch_rows, pick_question, publish_row
from ingest_di_yearbooks import CHAPTER_NO, OUT, SUBJECT
from retry_di_tops import crop_page_top, observe, spec_of

def main() -> int:
    env = p.load_env()
    limiter = p.RateLimiter(60)
    skeleton = json.loads((OUT / "all_skeleton.json").read_text(encoding="utf-8"))
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, CHAPTER_NO, SUBJECT)
    db = fetch_rows(sb, chapter_id)

    jul4 = {
        "body": (
            r"Let $f$ be a twice differentiable function on $\mathbb{R}$. "
            r"If $f'(0)=4$ and $f(x)+\int_{0}^{x}(x-t)f'(t)\,dt=(e^{2x}+e^{-2x})\cos 2x+\frac{2}{a}x$ "
            r"then $(2a+1)^{5}a^{2}$ is equal to"
        ),
        "options": None,
    }
    jul5 = json.loads((OUT / "2022-jul" / "gemma4" / "page_002.json").read_text(encoding="utf-8"))
    a_n = next(q for q in jul5["questions"] if int(q["q_no"]) == 6)
    for pdf_q, key, kind, entry in (
        (4, "8", "numerical", jul4),
        (5, "5", "numerical", {"body": a_n["body"], "options": None}),
    ):
        sk = next(r for r in skeleton if r["booklet"] == "2022-jul" and int(r["q_no"]) == pdf_q)
        spec = spec_of("2022-jul", pdf_q, key, kind, sk)
        ok, reason = publish_row(sb, db[("2022-jul", pdf_q)], spec, entry, env, limiter)
        print(f"2022-jul Q{pdf_q} {reason}", flush=True)

    jun5 = {
        "body": (
            r"The value of $\int_{0}^{\pi}\frac{e^{\cos x}\sin x}{(1+\cos^{2}x)(e^{\cos x}+e^{-\cos x})}\,dx$ is equal to"
        ),
        "options": [r"$\frac{\pi^{2}}{4}$", r"$\frac{\pi^{2}}{2}$", r"$\frac{\pi}{4}$", r"$\frac{\pi}{2}$"],
    }
    jun6_body = db[("2022-jun", 7)]["body"]
    opts6 = (
        sb.table("pyq_question_options")
        .select("option_index,body")
        .eq("question_id", db[("2022-jun", 7)]["id"])
        .execute()
        .data
        or []
    )
    jun6 = {
        "body": jun6_body,
        "options": [row["body"] for row in sorted(opts6, key=lambda r: r["option_index"])],
    }
    sk5 = next(r for r in skeleton if r["booklet"] == "2022-jun" and int(r["q_no"]) == 5)
    sk6 = next(r for r in skeleton if r["booklet"] == "2022-jun" and int(r["q_no"]) == 6)
    ok, reason = publish_row(sb, db[("2022-jun", 5)], spec_of("2022-jun", 5, "C", "mcq", sk5), jun5, env, limiter)
    print(f"2022-jun Q5 {reason}", flush=True)
    ok, reason = publish_row(sb, db[("2022-jun", 6)], spec_of("2022-jun", 6, "D", "mcq", sk6), jun6, env, limiter)
    print(f"2022-jun Q6 {reason}", flush=True)

    sk7 = next(r for r in skeleton if r["booklet"] == "2022-jun" and int(r["q_no"]) == 7)
    spec7 = spec_of("2022-jun", 7, "D", "mcq", sk7)
    from ingest_di_yearbooks import BOOKLETS
    pdf = next(b["pdf"] for b in BOOKLETS if b["id"] == "2022-jun")
    png = OUT / "2022-jun" / "crops" / "q07_region.png"
    import pymupdf
    doc = pymupdf.open(str(pdf))
    page = doc[2]
    hits = page.search_for("Q7 -")
    start = min(hits, key=lambda r: r.y0)
    clip = pymupdf.Rect(page.rect.x0, start.y0 - 4, page.rect.x1 * 0.72, page.rect.y1 - 40)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(200 / 72, 200 / 72), clip=clip, alpha=False)
    pix.save(str(png))
    doc.close()
    data = observe(png, spec7, env, limiter)
    raw = pick_question(data, 7) or data
    ok, reason = publish_row(sb, db[("2022-jun", 7)], spec7, {
        "body": raw.get("body") or "", "options": raw.get("options"), "page": 3,
    }, env, limiter)
    print(f"2022-jun Q7 {reason}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
