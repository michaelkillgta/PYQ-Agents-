import json
import sys
import pymupdf
sys.stdout.reconfigure(encoding='utf-8')

from pyq_common import configure_book, load_skeleton, load_answer_key
configure_book("math")

doc = pymupdf.open(r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")
skel = load_skeleton()
key_book = load_answer_key()
ch8_skel = {s["q_no"]: s for s in skel if s.get("chapter_no") == 8}
ch8_key = key_book.get("8", {}).get("answers", {})

held_qs = [17, 30, 31, 38, 45, 50, 57, 60, 73, 74, 76, 91, 93, 95, 96, 103, 105, 107]

for q in held_qs:
    spec = ch8_skel[q]
    pno = spec["page"]
    page = doc[pno - 1]
    
    same_col = [
        s for s in ch8_skel.values()
        if s["page"] == pno and s.get("column") == spec.get("column") and s["bbox"][1] > spec["bbox"][1] + 2
    ]
    if same_col:
        nxt = min(same_col, key=lambda s: s["bbox"][1])
        y1 = nxt["bbox"][1] - 2
    else:
        y1 = page.rect.y1 - 36
    
    x0, y0, x1, _ = spec["bbox"]
    rect = pymupdf.Rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    text = page.get_text("text", clip=rect).strip()
    k = ch8_key.get(str(q), {})
    col = spec.get("column")
    print(f"*** Q{q} (Page {pno}, Col {col}, Rect: {rect}, Key: {k}) ***")
    print(text)
    print("-" * 60)
