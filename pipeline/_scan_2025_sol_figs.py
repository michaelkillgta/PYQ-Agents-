"""See whether 2025 solution pages have embedded drawings."""
from pathlib import Path
import pymupdf

JAN = Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf")
APR = Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf")


def scan(label, pdf, a, b):
    doc = pymupdf.open(pdf)
    print(label)
    for i in range(a - 1, b):
        page = doc[i]
        imgs = page.get_images(full=True)
        drawings = page.get_drawings()
        if imgs or len(drawings) > 8:
            print(f"  p{i+1} images={len(imgs)} drawings={len(drawings)}")
    doc.close()


if __name__ == "__main__":
    scan("JAN 128-147", JAN, 128, 147)
    scan("APR 118-132", APR, 118, 132)
