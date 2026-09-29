"""Diagnose 2025 paper OCR katex holds and figure sizes."""
from __future__ import annotations

import json
from pathlib import Path

from agents.katex_check import (
    _MATH_INNER,
    _MATH_SPLIT,
    _NAKED_CMD,
    dollar_runs_ok,
    leftover_latex_outside_math,
    probe_tex,
    smashed_tex,
)
from ingest_math_2025_paper_solutions import BOOKS, tidy_paper
from ingest_math_2026_jan_di_solutions import assemble_solution_md


def main() -> None:
    packets = json.loads(
        Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions\packets.json").read_text(encoding="utf-8")
    )
    holds = [x for x in packets if x.get("hold") == "katex_render"]
    print("katex holds", [(h["booklet"], h["section"], h["pdf_q"]) for h in holds])
    for h in holds:
        book = next(b for b in BOOKS if b["id"] == h["booklet"])
        cache = book["out"] / "ocr" / f"{h['section']}_q{h['pdf_q']:02d}.json"
        data = json.loads(cache.read_text(encoding="utf-8"))
        raw = str(data.get("markdown") or data.get("text") or "")
        md = tidy_paper(assemble_solution_md(h["pdf_q"], raw, has_diagram=False))
        print("=" * 60, h["booklet"], h["section"], h["pdf_q"])
        print(
            "dollars", md.count("$"),
            "ok", dollar_runs_ok(md),
            "leftover", leftover_latex_outside_math(md),
            "smashed", smashed_tex(md),
            "len", len(md),
        )
        if leftover_latex_outside_math(md):
            for part in _MATH_SPLIT.split(md):
                if part.startswith("$") and part.endswith("$"):
                    continue
                m = _NAKED_CMD.search(part)
                if m:
                    i = m.start()
                    print(" leftover", repr(part[max(0, i - 40): i + 50]))
        bad = 0
        for m in _MATH_INNER.finditer(md):
            if not probe_tex(m.group(1)):
                bad += 1
                if bad <= 4:
                    print(" probe fail", m.group(1)[:180])
        print(" probe fails", bad)
        print(md[:500])

    print("--- figure sizes ---")
    for d in (
        Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-solutions\figures"),
        Path(r"c:\Users\tempo\Downloads\files\out-math-2025-apr-solutions\figures"),
    ):
        for f in sorted(d.glob("*.png")):
            print(f"{f.name:28} {f.stat().st_size:8}")


if __name__ == "__main__":
    main()
