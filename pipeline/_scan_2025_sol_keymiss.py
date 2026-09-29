"""Inspect headings whose printed key did not parse."""
from pathlib import Path
import re
import pymupdf
from pyq_ocr_inventory import _page_lines

JAN = Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf")
Q_HEAD = re.compile(r"^Q\s*(\d+)\s*\.\s*$")


def dump(page_no: int, around_y: float):
    doc = pymupdf.open(JAN)
    page = doc[page_no - 1]
    recs = sorted(_page_lines(page), key=lambda r: (r["y0"], r["x0"]))
    print(f"\n=== p{page_no} around y={around_y} ===")
    for rec in recs:
        if abs(rec["y0"] - around_y) < 50:
            print(f"  x={rec['x0']:6.1f} y={rec['y0']:6.1f} {rec['text']!r}")
    doc.close()


if __name__ == "__main__":
    dump(132, 281)  # Q11
    dump(143, 302)  # DE Q4
    dump(144, 378)  # DE Q6
    dump(144, 638)  # DE Q7
