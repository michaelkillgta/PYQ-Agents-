"""Inventory Qn. heading positions on 2025 solution pages."""
from __future__ import annotations

import re
from pathlib import Path

import pymupdf

from pyq_ocr_inventory import _page_lines, page_chapter_title

JAN = Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf")
APR = Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf")

Q_HEAD = re.compile(r"^Q\s*(\d+)\s*\.\s*$")
KEY_ONLY = re.compile(r"^\(([^)]+)\)\s*$")
TITLES = {
    "Definite Integration",
    "Area Under Curves",
    "Differential Equations",
}


def headings(page) -> list[dict]:
    recs = sorted(_page_lines(page), key=lambda r: (r["y0"], r["x0"]))
    out = []
    for i, rec in enumerate(recs):
        m = Q_HEAD.match(rec["text"].replace("\xa0", " ").strip())
        if not m:
            continue
        key = None
        for nxt in recs[i + 1 : i + 8]:
            if abs(nxt["x0"] - rec["x0"]) < 40 and nxt["y0"] >= rec["y0"] - 2:
                km = KEY_ONLY.match(nxt["text"].strip())
                if km:
                    key = km.group(1).strip()
                    break
            if nxt["y0"] > rec["y0"] + 40:
                break
        col = "L" if rec["x0"] < page.rect.width * 0.48 else "R"
        out.append({
            "q": int(m.group(1)),
            "key": key,
            "x": rec["x0"],
            "y0": rec["y0"],
            "y1": rec["y1"],
            "col": col,
        })
    return out


def scan(label, pdf, start, end):
    doc = pymupdf.open(pdf)
    print("=" * 70, label)
    by_title: dict[str, list] = {}
    for i in range(start - 1, min(end, doc.page_count)):
        page = doc[i]
        title = page_chapter_title(page)
        if title not in TITLES:
            continue
        hs = headings(page)
        by_title.setdefault(title, [])
        print(f" p{i+1:3} {title:24} n={len(hs):2}", " ".join(f"{h['col']}{h['q']}({h['key']})@{h['y0']:.0f}" for h in hs))
        by_title[title].extend({"page": i + 1, **h} for h in hs)
    for title, hs in by_title.items():
        qs = sorted({h["q"] for h in hs})
        print(f"  {title}: printed {qs} count={len(qs)}")
    doc.close()


if __name__ == "__main__":
    scan("JAN sols 120-160", JAN, 120, 160)
    scan("APR sols 110-150", APR, 110, 150)
