#!/usr/bin/env python3
"""Dump clipped PDF text + answer keys for every held Parabola (ch 24) question."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pymupdf

sys.stdout.reconfigure(encoding="utf-8")

from pyq_common import configure_book, load_answer_key, load_skeleton

CHAPTER_NO = 24
HELD = [
    11, 12, 13, 14, 15, 16, 17, 18, 19, 29, 33, 44, 45, 46, 47, 48, 49, 50,
    51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
    69, 70, 71, 72, 73, 74, 75, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98,
    99, 100, 101, 102, 103, 104,
]

configure_book("math")
doc = pymupdf.open(r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")
skel = load_skeleton()
key_book = load_answer_key()
ch_skel = {s["q_no"]: s for s in skel if s.get("chapter_no") == CHAPTER_NO}
ch_key = key_book.get(str(CHAPTER_NO), {}).get("answers", {})

pages = sorted({ch_skel[q]["page"] for q in HELD if q in ch_skel})
print(f"Held pages: {pages[0]}-{pages[-1]} ({len(pages)} pages)")
print(f"Skeleton q range: {min(ch_skel)}-{max(ch_skel)} n={len(ch_skel)}")

records = []
for q in HELD:
    spec = ch_skel[q]
    pno = spec["page"]
    page = doc[pno - 1]
    k = ch_key.get(str(q), {})
    col = spec.get("column")
    x0, y0, x1, y1 = spec["bbox"]

    same_col = [
        s
        for s in skel
        if s.get("chapter_no") == CHAPTER_NO
        and s["page"] == pno
        and s.get("column") == spec.get("column")
        and s["bbox"][1] > y0 + 2
        and int(s["q_no"]) != q
    ]
    if same_col:
        nxt = min(same_col, key=lambda s: s["bbox"][1])
        clip_y1 = nxt["bbox"][1] - 2
    else:
        clip_y1 = page.rect.y1 - 20

    clip = pymupdf.Rect(x0 - 4, y0 - 4, x1 + 4, clip_y1 + 4)
    pdf_text = page.get_text("text", clip=clip).strip()

    cont_text = ""
    if not same_col:
        if col == "L":
            rights = [
                s
                for s in skel
                if s.get("chapter_no") == CHAPTER_NO
                and s["page"] == pno
                and s.get("column") == "R"
            ]
            if rights:
                first = min(rights, key=lambda s: s["bbox"][1])
                fx0, _, fx1, _ = first["bbox"]
                fy1 = first["bbox"][1] - 2
                fy0 = max(page.rect.y0 + 36, fy1 - 140)
                cont_text = page.get_text(
                    "text", clip=pymupdf.Rect(fx0, fy0, fx1, fy1)
                ).strip()
        elif col == "R" and pno < doc.page_count:
            nxt_page = doc[pno]
            lefts = [
                s
                for s in skel
                if s.get("chapter_no") == CHAPTER_NO
                and s["page"] == pno + 1
                and s.get("column") == "L"
            ]
            if lefts:
                first = min(lefts, key=lambda s: s["bbox"][1])
                fx0, _, fx1, _ = first["bbox"]
                fy1 = first["bbox"][1] - 2
            else:
                fx0, fx1 = 38.0, nxt_page.rect.width / 2
                fy1 = min(nxt_page.rect.y0 + 220, nxt_page.rect.y1 - 8)
            fy0 = nxt_page.rect.y0 + 36
            cont_text = nxt_page.get_text(
                "text", clip=pymupdf.Rect(fx0, fy0, fx1, fy1)
            ).strip()

    rec = {
        "q_no": q,
        "page": pno,
        "column": col,
        "answer_type": spec.get("answer_type"),
        "key": k,
        "figure_keys": spec.get("figure_keys") or [],
        "pdf_text": pdf_text,
        "cont_text": cont_text,
    }
    records.append(rec)

    print("=" * 88)
    print(
        f"Q{q} | Page {pno} Col {col} | type={spec.get('answer_type')} "
        f"| key={k} | figs={spec.get('figure_keys')}"
    )
    print("--- PDF ---")
    print(pdf_text)
    if cont_text:
        print("--- CONT ---")
        print(cont_text)

out = Path("out-math/agents/chapter_24/held_pdf_dump.json")
out.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nWrote {out} ({len(records)} records)")
