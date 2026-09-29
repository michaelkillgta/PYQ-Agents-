"""Dump Qn.(key) heading positions on 2025 solution pages."""
from __future__ import annotations

import re
from pathlib import Path

import pymupdf

from pyq_ocr_inventory import _page_lines, MATH_CHAPTER_TITLES, page_chapter_title

JAN = Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf")
APR = Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf")

Q_SOL = re.compile(r"^Q\s*(\d+)\s*\.\s*\(([^)]+)\)")


def dump_book(label: str, pdf: Path, pages: list[int]) -> None:
    doc = pymupdf.open(pdf)
    print("=" * 70, label, "w", round(doc[0].rect.width), "h", round(doc[0].rect.height))
    for pn in pages:
        page = doc[pn - 1]
        title = page_chapter_title(page)
        print(f"\n--- page {pn} title={title!r}")
        recs = []
        for rec in _page_lines(page):
            m = Q_SOL.match(rec["text"])
            if not m:
                continue
            recs.append((rec["x0"], rec["y0"], rec["y1"], rec["text"][:50], m.group(1), m.group(2)))
        recs.sort(key=lambda r: (r[1], r[0]))
        for x0, y0, y1, txt, q, k in recs:
            col = "L" if x0 < page.rect.width * 0.48 else "R"
            print(f"  {col} x={x0:6.1f} y={y0:6.1f}-{y1:6.1f} {txt}")
    doc.close()


def toc_solutions(pdf: Path) -> None:
    doc = pymupdf.open(pdf)
    print("\n### TOC page 3 first 80 lines")
    text = doc[2].get_text("text") or ""
    for i, line in enumerate(text.splitlines()[:80], 1):
        if line.strip():
            print(f"{i:3} {line.strip()}")
    print("\n### last 8 pages titles")
    for i in range(max(1, doc.page_count - 8), doc.page_count + 1):
        print(i, page_chapter_title(doc[i - 1]), (doc[i - 1].get_text("text") or "").splitlines()[:2])
    doc.close()


if __name__ == "__main__":
    dump_book("JAN", JAN, [126, 128, 129, 132, 133, 134])
    dump_book("APR", APR, [116, 118, 119, 120, 121])
    toc_solutions(JAN)
