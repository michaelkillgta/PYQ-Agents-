#!/usr/bin/env python3
"""
Stage 1 — Deterministic extraction (no AI, no cost, ~2 minutes).

Pulls out of the PYQ PDF:
  1. Every figure as a clean PNG (watermark overlay filtered out)
  2. A manifest of figure -> page, bbox, column, size
  3. The answer key (chapter -> question number -> answer)
  4. Per-page rasters for the Stage-2 VLM pass

Usage:
    python extract_assets.py book.pdf ./out
"""
import json
import re
import sys
from pathlib import Path

import pymupdf

# The mathongo watermark is a full-page overlay image. Anything covering
# >85% of the page in both axes is the watermark, not content.
WATERMARK_COVERAGE = 0.85
# Ignore hairline spacers / transparency masks.
MIN_FIGURE_PT = 18


def extract_figures(doc, out_dir):
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for pno in range(len(doc)):
        page = doc[pno]
        pw, ph = page.rect.width, page.rect.height
        mid_x = pw / 2  # 2-column layout: which column does this figure sit in?

        for info in page.get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            w, h = x1 - x0, y1 - y0

            if w > WATERMARK_COVERAGE * pw and h > WATERMARK_COVERAGE * ph:
                continue  # watermark overlay
            if w < MIN_FIGURE_PT or h < MIN_FIGURE_PT:
                continue  # spacer / mask

            xref = info["xref"]
            pix = pymupdf.Pixmap(doc, xref)
            if pix.n - pix.alpha > 3:  # CMYK/ICC -> RGB
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            if pix.alpha:  # flatten transparency onto white
                pix = pymupdf.Pixmap(pix, 0)

            name = f"p{pno + 1:03d}_x{xref}.png"
            pix.save(str(fig_dir / name))

            manifest.append({
                "figure_key": f"p{pno + 1:03d}_x{xref}",
                "file": f"figures/{name}",
                "page": pno + 1,
                "bbox": [round(v, 1) for v in (x0, y0, x1, y1)],
                "column": "left" if x0 < mid_x else "right",
                "px_width": pix.width,
                "px_height": pix.height,
                "bytes": len(pix.tobytes("png")),
            })
            pix = None

    return manifest


def extract_answer_key(doc, start_hint=450):
    """Answer keys live at the back: '1. Mathematics in Physics' then 'Q1 (4)'."""
    text = ""
    for pno in range(start_hint, len(doc)):
        t = doc[pno].get_text()
        if "Answer Key" in t or text:
            text += t

    chapter_re = re.compile(r"^\s*(\d{1,2})\.\s+([A-Z][A-Za-z ,\-&']+?)\s*$", re.M)
    token_re = re.compile(r"Q(\d+)\s*\(([^)]+)\)")

    marks = [(m.start(), int(m.group(1)), m.group(2).strip())
             for m in chapter_re.finditer(text)]
    key = {}
    for i, (pos, num, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        answers = {}
        for q, a in token_re.findall(text[pos:end]):
            a = a.strip()
            answers[int(q)] = {
                # 1-4 => MCQ option index. Anything else => numerical answer.
                "type": "mcq" if a in {"1", "2", "3", "4"} else "numerical",
                "value": a,
            }
        key[num] = {"chapter_no": num, "title": title, "answers": answers}
    return key


def rasterize_pages(doc, out_dir, dpi=200, last_content_page=454):
    """Page images for the Stage-2 VLM pass. Skip the answer-key tail."""
    pg_dir = out_dir / "pages"
    pg_dir.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72
    mat = pymupdf.Matrix(zoom, zoom)
    written = []
    for pno in range(last_content_page):
        pix = doc[pno].get_pixmap(matrix=mat)
        name = f"page_{pno + 1:03d}.png"
        pix.save(str(pg_dir / name))
        written.append(name)
    return written


def main():
    pdf_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "./out")
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(pdf_path)

    figures = extract_figures(doc, out_dir)
    (out_dir / "figures.json").write_text(json.dumps(figures, indent=2))

    key = extract_answer_key(doc)
    (out_dir / "answer_key.json").write_text(json.dumps(key, indent=2))

    total_answers = sum(len(c["answers"]) for c in key.values())
    print(f"figures extracted : {len(figures)}")
    print(f"chapters in key   : {len(key)}")
    print(f"answers parsed    : {total_answers}")
    print(f"figure bytes      : {sum(f['bytes'] for f in figures) / 1e6:.1f} MB")
    print(f"pages with figures: {len({f['page'] for f in figures})}")

    if "--rasterize" in sys.argv:
        pages = rasterize_pages(doc, out_dir)
        print(f"page rasters      : {len(pages)}")


if __name__ == "__main__":
    main()
