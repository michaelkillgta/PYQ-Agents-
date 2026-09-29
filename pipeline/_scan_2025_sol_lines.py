"""Dump raw solution-page lines to see heading glyphs."""
from pathlib import Path

import pymupdf

from pyq_ocr_inventory import _page_lines, page_chapter_title, page_text

JAN = Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf")


def main():
    doc = pymupdf.open(JAN)
    for pn in (128, 129, 130):
        page = doc[pn - 1]
        print("=" * 70, "page", pn, "title", page_chapter_title(page), "w", page.rect.width)
        recs = sorted(_page_lines(page), key=lambda r: (r["y0"], r["x0"]))
        print("n_lines", len(recs))
        for rec in recs[:60]:
            t = rec["text"].replace("\n", "\\n")
            print(f"  x={rec['x0']:6.1f} y={rec['y0']:6.1f} {t[:90]!r}")
        print("--- get_text first 25 nonempty ---")
        n = 0
        for line in (page_text(page) or "").splitlines():
            if not line.strip():
                continue
            print(repr(line.strip()[:100]))
            n += 1
            if n >= 25:
                break
    doc.close()


if __name__ == "__main__":
    main()
