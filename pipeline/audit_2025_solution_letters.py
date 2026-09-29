#!/usr/bin/env python3
"""Compare every 2025 paper write-up clip's PDF text layer to live solution_md."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf

import pyq_common as p
from ingest_math_2025_paper_solutions import (
    BOOKS,
    SECTION_SLUG,
    crop_rect,
    fetch_rows,
    section_of,
)
from ingest_math_2026_jan_di_solutions import ANY_FIG
from layout_math_2026_jan_di_steps import paper_lines

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")
NOISE = re.compile(
    r"mathongo|www\.mathongo|paperphodnahai|\bmi\b|jee main 2025|"
    r"chapter-wise question bank|definite integration|area under curves|"
    r"differential equations",
    re.I,
)
LISTING = re.compile(r"^(?:Q\s*)?\d{1,2}\.\s*(?:\([^)]+\)\s*)?")


def skeleton(s: str) -> str:
    s = (s or "").lower().replace("−", "-").replace("–", "-").replace("×", "x")
    s = re.sub(r"\\[a-z]+", "", s)
    s = ANY_FIG.sub("", s)
    s = re.sub(r"[^a-z0-9=+\-()]", "", s)
    return s


def clip_lines(doc, spec: dict) -> list[str]:
    page = doc[spec["page"] - 1]
    clip = crop_rect(page, spec)
    blocks = page.get_text("blocks", clip=clip) or []
    lines: list[str] = []
    for b in sorted(blocks, key=lambda t: (round(t[1], 1), t[0])):
        t = " ".join(str(b[4] or "").split())
        if not t or NOISE.search(t) and len(skeleton(t)) < 12:
            continue
        if NOISE.fullmatch(t.strip()):
            continue
        t = LISTING.sub("", t, count=1).strip()
        t = re.sub(r"\bmathongo\b", " ", t, flags=re.I)
        t = " ".join(t.split())
        if t:
            lines.append(t)
    cont = spec.get("continuation")
    if spec.get("continues") and cont:
        page2 = doc[int(cont["page"]) - 1]
        band = pymupdf.Rect(
            page2.rect.x0,
            page2.rect.y0 + 40,
            page2.rect.x1,
            float(cont.get("cut_y") or page2.rect.y0 + 220) - 4,
        )
        for b in sorted(page2.get_text("blocks", clip=band) or [], key=lambda t: (round(t[1], 1), t[0])):
            t = " ".join(str(b[4] or "").split())
            t = re.sub(r"\bmathongo\b", " ", t, flags=re.I)
            t = " ".join(t.split())
            if not t or (NOISE.search(t) and len(skeleton(t)) < 12):
                continue
            lines.append(t)
    return lines


def missing_from(pdf_lines: list[str], md: str) -> list[dict]:
    hay = skeleton("\n".join(paper_lines(md)))
    out = []
    for i, line in enumerate(pdf_lines):
        sk = skeleton(line)
        if len(sk) < 3:
            continue
        if sk in hay:
            continue
        # allow tiny OCR/latex spelling drift of 1 char on long lines
        if len(sk) >= 16:
            hit = False
            for n in range(len(sk) - 8):
                if sk[n : n + 10] in hay:
                    hit = True
                    break
            if hit and sum(ch in hay for ch in sk) / len(sk) > 0.85:
                continue
        out.append({"i": i, "line": line, "sk": sk})
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    env = p.load_env()
    sb = p.supabase_client()
    chapter_id = p.resolve_chapter_id(sb, 17, "Mathematics")
    db_rows = fetch_rows(sb, chapter_id)
    print(f"live 2025 rows {len(db_rows)}", flush=True)

    reports = []
    for book in BOOKS:
        inv = json.loads((book["out"] / "inventory.json").read_text(encoding="utf-8"))
        doc = pymupdf.open(book["pdf"])
        for ch in inv["chapters"]:
            slug = SECTION_SLUG[ch["title"]]
            for spec in ch["crop_plan"]:
                pdf_q = int(spec["q_no"])
                row = db_rows.get((book["id"], slug, pdf_q))
                pdf_lines = clip_lines(doc, spec)
                md = "" if row is None else (row.get("solution_md") or "")
                miss = missing_from(pdf_lines, md)
                rec = {
                    "booklet": book["id"],
                    "section": slug,
                    "pdf_q": pdf_q,
                    "row_id": None if row is None else row["id"],
                    "db_q": None if row is None else row.get("q_no"),
                    "pdf_line_count": len(pdf_lines),
                    "pdf_lines": pdf_lines,
                    "missing": miss,
                    "live_preview": md[:240],
                }
                reports.append(rec)
                tag = "MISS" if miss else "ok"
                extra = ""
                if miss:
                    extra = " | " + " || ".join(m["line"][:80] for m in miss[:4])
                print(
                    f"  [{tag}] {book['id']} {slug} Q{pdf_q:02d} "
                    f"pdf_lines={len(pdf_lines)} missing={len(miss)}{extra}",
                    flush=True,
                )
        doc.close()

    flagged = [r for r in reports if r["missing"]]
    dump_path = ROOT / "letter_audit.json"
    dump_path.write_text(json.dumps(reports, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"flagged {len(flagged)}/{len(reports)} -> {dump_path}", flush=True)
    return 0 if not flagged else 2


if __name__ == "__main__":
    raise SystemExit(main())
