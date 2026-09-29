#!/usr/bin/env python3
"""Inventory Definite Integration questions in the 2025 Jan / April chapter-wise PDFs.

No model spend. Run January and April in parallel.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf

BOOKS = [
    {
        "id": "2025-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf"),
        "expect": 37,
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-di"),
    },
    {
        "id": "2025-apr",
        "pdf": Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf"),
        "expect": 28,
        "out": Path(r"c:\Users\tempo\Downloads\files\out-math-2025-apr-di"),
    },
]

Q_HEAD = re.compile(r"(?:^|\n)\s*Q\s*(\d+)\s*[\.\:\-–]", re.I)
DI_HDR = re.compile(r"definite\s+integration", re.I)
INDEF_HDR = re.compile(r"indefinite\s+integration", re.I)
AUC_HDR = re.compile(r"area\s+under\s+curves?", re.I)
SOLUTIONS = re.compile(r"^\s*solutions\s*$", re.I)
ANSWER_KEYS = re.compile(r"answer\s+keys?", re.I)
CHAPTER_LINE = re.compile(
    r"^\s*(\d{1,2})\.\s*(basic of mathematics|quadratic|complex|sequences|"
    r"permutation|binomial|statistics|matrices|determinants|probability|"
    r"sets and relations|functions|limits|continuity|application of derivatives|"
    r"indefinite integration|definite integration|area under|differential|"
    r"straight lines|circle|parabola|ellipse|hyperbola|trigonometric|"
    r"inverse trigonometric|vector algebra|three dimensional)",
    re.I,
)


def page_text(page) -> str:
    return page.get_text("text") or ""


def running_header(text: str) -> str:
    head = "\n".join(text.splitlines()[:8])
    return head


def inventory_book(spec: dict) -> dict:
    doc = pymupdf.open(spec["pdf"])
    n = doc.page_count
    pages = []
    solutions_start = None
    answer_key_pages = []
    for i in range(n):
        text = page_text(doc[i])
        head = running_header(text)
        if solutions_start is None and SOLUTIONS.search(text.split("\n", 1)[0] if text else ""):
            # Solutions TOC often titled "Solutions" as a page heading
            if re.search(r"(?m)^\s*Solutions\s*$", text[:400]):
                solutions_start = i + 1
        if ANSWER_KEYS.search(head) or ANSWER_KEYS.search(text[:200]):
            answer_key_pages.append(i + 1)
        pages.append({
            "page": i + 1,
            "di_header": bool(DI_HDR.search(head) and not INDEF_HDR.search(head[:80])),
            "indef_header": bool(INDEF_HDR.search(head)),
            "auc_header": bool(AUC_HDR.search(head)),
            "q_nos": [int(m) for m in Q_HEAD.findall(text)],
            "di_anywhere": bool(DI_HDR.search(text)),
            "preview": " ".join(text.split())[:180],
        })
    if solutions_start is None:
        # fallback: large jump to solutions TOC around last third
        for row in pages:
            if re.search(r"(?m)^\s*Solutions\s*$", row["preview"]):
                solutions_start = row["page"]
                break

    q_section = [r for r in pages if solutions_start is None or r["page"] < solutions_start]
    di_pages = [r for r in q_section if r["di_header"]]
    # Walk header until next distinct chapter
    di_run = []
    started = False
    for r in q_section:
        if r["di_header"]:
            started = True
        if started and r["auc_header"] and not r["di_header"]:
            break
        if started:
            if r["di_header"] or (r["q_nos"] and not r["indef_header"] and not r["auc_header"]):
                di_run.append(r)
            elif r["auc_header"] or r["indef_header"]:
                break

    leftover = [
        r for r in q_section
        if r["page"] not in {x["page"] for x in di_run}
        and r["di_anywhere"]
        and not r["indef_header"]
        and r["page"] not in answer_key_pages
    ]

    q_from_run = []
    seen = set()
    for r in di_run:
        for q in r["q_nos"]:
            key = (r["page"], q)
            if key in seen:
                continue
            seen.add(key)
            q_from_run.append({"page": r["page"], "q_no": q})

    key_text = []
    for pno in answer_key_pages:
        key_text.append({"page": pno, "text": page_text(doc[pno - 1])[:4000]})
    doc.close()

    report = {
        "id": spec["id"],
        "pdf": str(spec["pdf"]),
        "page_count": n,
        "expect": spec["expect"],
        "solutions_start": solutions_start,
        "answer_key_pages": answer_key_pages,
        "di_header_pages": [r["page"] for r in di_pages],
        "di_run_pages": [r["page"] for r in di_run],
        "di_run_q": q_from_run,
        "di_run_count": len(q_from_run),
        "leftover_di_mentions": [{"page": r["page"], "q_nos": r["q_nos"]} for r in leftover],
        "unique_q_nos_in_run": sorted({x["q_no"] for x in q_from_run}),
        "gate_ok": len(q_from_run) == spec["expect"]
        or len({x["q_no"] for x in q_from_run}) == spec["expect"],
        "key_preview": key_text[:3],
        "di_page_previews": [
            {"page": r["page"], "q_nos": r["q_nos"], "preview": r["preview"]}
            for r in di_run
        ],
    }
    out = spec["out"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "inventory.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return report


def main() -> int:
    with ThreadPoolExecutor(max_workers=2) as pool:
        reports = list(pool.map(inventory_book, BOOKS))
    for r in reports:
        print(
            f"{r['id']}: pages={r['page_count']} di_run={r['di_run_pages']} "
            f"q_count={r['di_run_count']} unique={r['unique_q_nos_in_run']} "
            f"expect={r['expect']} gate_ok={r['gate_ok']} "
            f"keys={r['answer_key_pages']} leftover={r['leftover_di_mentions']}",
            flush=True,
        )
        for p in r["di_page_previews"]:
            print(f"  p{p['page']} Q{p['q_nos']} {p['preview'][:120]}", flush=True)
    return 0 if all(r["gate_ok"] for r in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())
