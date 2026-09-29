"""Inspect remaining 2025 paper-OCR holds."""
from __future__ import annotations

import json
from pathlib import Path

from agents.katex_check import (
    _MATH_INNER,
    dollar_runs_ok,
    leftover_latex_outside_math,
    probe_tex,
    smashed_tex,
)
from ingest_math_2025_paper_solutions import BOOKS, tidy_paper
from ingest_math_2026_jan_di_solutions import assemble_solution_md

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")


def main() -> None:
    packets = json.loads((ROOT / "packets.json").read_text(encoding="utf-8"))
    holds = [x for x in packets if x.get("hold")]
    print("holds", len(holds))
    for h in holds:
        print("-", h["booklet"], h["section"], h["pdf_q"], h["hold"][:80])
        book = next(b for b in BOOKS if b["id"] == h["booklet"])
        cache = book["out"] / "ocr" / f"{h['section']}_q{h['pdf_q']:02d}.json"
        print("  cache", cache.exists(), cache)
        if not cache.exists():
            continue
        data = json.loads(cache.read_text(encoding="utf-8"))
        raw = str(data.get("markdown") or data.get("text") or "")
        md = tidy_paper(assemble_solution_md(h["pdf_q"], raw, has_diagram=False))
        print(
            "  dollars", md.count("$"),
            "pair", dollar_runs_ok(md),
            "leftover", leftover_latex_outside_math(md),
            "smashed", smashed_tex(md),
        )
        bad = 0
        for m in _MATH_INNER.finditer(md):
            if not probe_tex(m.group(1)):
                bad += 1
                if bad <= 3:
                    print("  probe", m.group(1)[:200])
        print("  probe fails", bad)
        print(md[:700])
        print("---")


if __name__ == "__main__":
    main()
