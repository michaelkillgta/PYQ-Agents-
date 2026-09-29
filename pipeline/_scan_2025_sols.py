"""Scan 2025 Jan/Apr maths PDFs for printed solution write-ups."""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf

from pyq_ocr_inventory import SOL_HEAD_LINE, find_answers_solutions_page, _page_lines

BOOKS = [
    ("2025-jan", Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf")),
    ("2025-apr", Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf")),
]

DI = re.compile(r"definite\s+integration", re.I)
AUC = re.compile(r"area\s+under", re.I)
DE = re.compile(r"differential\s+equations?", re.I)
SOL = re.compile(r"^\s*solutions?\s*$", re.I)
ANS_SOL = re.compile(r"answers?\s+and\s+solutions?", re.I)


def scan(spec):
    bid, pdf = spec
    doc = pymupdf.open(pdf)
    answers = find_answers_solutions_page(doc)
    sol_pages = []
    di_sol = []
    heads = []
    for i in range(doc.page_count):
        page = doc[i]
        text = page.get_text("text") or ""
        first = "\n".join(text.splitlines()[:6])
        last = "\n".join(text.splitlines()[-8:])
        footer_di = bool(DI.search(text))
        if SOL.search(text[:80]) or ANS_SOL.search(first) or "Solutions" in first:
            sol_pages.append(i + 1)
        if footer_di and (i + 1) > (answers or 0):
            n_heads = 0
            sample = []
            for rec in _page_lines(page):
                m = SOL_HEAD_LINE.match(rec["text"])
                if m:
                    n_heads += 1
                    if len(sample) < 4:
                        sample.append(rec["text"][:60])
            di_sol.append({"page": i + 1, "heads": n_heads, "sample": sample, "preview": " ".join(text.split())[:140]})
        if i < 3 or i > doc.page_count - 4:
            heads.append({"page": i + 1, "first": first.replace("\n", " | ")[:180]})
    # also pages after a Solutions TOC
    sol_heads_all = []
    for i in range(doc.page_count):
        page = doc[i]
        n = 0
        for rec in _page_lines(page)[:40]:
            if SOL_HEAD_LINE.match(rec["text"]):
                n += 1
        if n:
            tail = " ".join((page.get_text("text") or "").split()[-12:])
            sol_heads_all.append({"page": i + 1, "n": n, "tail": tail[:80]})
    doc.close()
    return {
        "id": bid,
        "pages": pymupdf.open(pdf).page_count if False else None,
        "answers_page": answers,
        "sol_heading_pages": sol_pages[:20],
        "di_sol_pages": di_sol[:15],
        "sol_head_pages": sol_heads_all[:25],
    }


def main():
    with ThreadPoolExecutor(max_workers=2) as pool:
        for r in pool.map(scan, BOOKS):
            # page count
            doc = pymupdf.open(dict(BOOKS)[r["id"]] if False else BOOKS[0][1] if r["id"]=="2025-jan" else BOOKS[1][1])
            r["pages"] = doc.page_count
            doc.close()
            print("=" * 60, r["id"], "pages", r["pages"], "answers", r["answers_page"])
            print("sol_heading_pages", r["sol_heading_pages"])
            print("sol_head n.(key) pages", r["sol_head_pages"])
            print("di_sol", r["di_sol_pages"])


if __name__ == "__main__":
    main()
