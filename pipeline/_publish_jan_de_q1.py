"""Publish January DE Q1 from the printed crop (OCR looped on textstyle)."""
from __future__ import annotations

from pathlib import Path

import pyq_common as p
from agents.katex_check import katex_render_ok
from ingest_math_2025_paper_solutions import dump, tidy_paper
from ingest_math_2026_jan_di_solutions import PAPER_MARKER, assemble_solution_md

MD = """
$\\frac{dy}{dx} + 2y \\tan x = \\sin x$
I.F. $= e^{2\\int \\tan x\\,dx} = \\sec^2 x$
$y \\sec^2 x = \\int \\frac{\\sin x}{\\cos^2 x}\\,dx$
$= \\int \\tan x \\sec x\\,dx$
$= \\sec x + C$
$C = -2$
$y = \\cos x - 2\\cos^2 x$
$y\\left(\\frac{\\pi}{4}\\right) = \\frac{1}{\\sqrt{2}} - 1$
$y' = -\\sin x + 4\\cos x\\sin x$
$y'\\left(\\frac{\\pi}{4}\\right) = -\\frac{1}{\\sqrt{2}} + 2$
$y'\\left(\\frac{\\pi}{4}\\right) + y\\left(\\frac{\\pi}{4}\\right) = 1$
"""


def main() -> int:
    packed = tidy_paper(assemble_solution_md(1, MD, has_diagram=False))
    print(packed)
    print("katex", katex_render_ok(packed))
    if not katex_render_ok(packed):
        return 2
    cache = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-jan-solutions\ocr\de_q01.json")
    dump(cache, {"pdf_q_no": 1, "answer": "1", "has_diagram": False, "markdown": MD.strip(), "_source": "crop-repair"})
    sb = p.supabase_client()
    sb.table("pyq_questions").update({"solution_md": packed}).eq(
        "id", "5df402b6-7686-4e65-a90b-f8d84058b0c9"
    ).execute()
    print("published jan de Q1", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
