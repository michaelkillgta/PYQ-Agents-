import json
import sys
import pymupdf
sys.stdout.reconfigure(encoding='utf-8')

from pyq_common import configure_book, load_skeleton, load_answer_key
configure_book("math")

doc = pymupdf.open(r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")
skel = load_skeleton()
key_book = load_answer_key()
ch9_skel = {s["q_no"]: s for s in skel if s.get("chapter_no") == 9}
ch9_key = key_book.get("9", {}).get("answers", {})

held_qs = [7, 14, 15, 18, 20, 31, 49, 54, 59, 62, 70, 74, 75, 77, 80, 82, 84, 85, 86, 90, 115, 150, 153]

# Load parsed.json from out-math/agents/chapter_9/parsed.json
with open("out-math/agents/chapter_9/parsed.json", "r", encoding="utf-8") as f:
    parsed = json.load(f)

for q in held_qs:
    spec = ch9_skel[q]
    pno = spec["page"]
    page = doc[pno - 1]
    k = ch9_key.get(str(q), {})
    col = spec.get("column")
    
    same_col = [
        s for s in ch9_skel.values()
        if s["page"] == pno and s.get("column") == spec.get("column") and s["bbox"][1] > spec["bbox"][1] + 2
    ]
    if same_col:
        nxt = min(same_col, key=lambda s: s["bbox"][1])
        y1 = nxt["bbox"][1] - 2
    else:
        y1 = page.rect.y1 - 36
    
    x0, y0, x1, _ = spec["bbox"]
    rect = pymupdf.Rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    pdf_text = page.get_text("text", clip=rect).strip()
    
    entry = parsed.get(str(q), {})
    
    print("=" * 80)
    print(f"Q{q} | Page: {pno} | Col: {col} | Type: {spec.get('answer_type')} | Key: {k}")
    print("=" * 80)
    print("--- RAW PDF TEXT ---")
    print(pdf_text)
    print("\n--- CURRENT PARSED.JSON ---")
    print(f"Body: {repr(entry.get('body'))}")
    print(f"Options: {entry.get('options')}")
    print("-" * 80)
