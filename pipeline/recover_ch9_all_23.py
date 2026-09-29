import json
import sys
import pymupdf
import re
sys.stdout.reconfigure(encoding='utf-8')

from pyq_common import configure_book, load_skeleton, load_answer_key
configure_book("math")

doc = pymupdf.open(r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")
skel = load_skeleton()
key_book = load_answer_key()
ch9_skel = {s["q_no"]: s for s in skel if s.get("chapter_no") == 9}
ch9_key = key_book.get("9", {}).get("answers", {})

held_qs = [7, 14, 15, 18, 20, 31, 49, 54, 59, 62, 70, 74, 75, 77, 80, 82, 84, 85, 86, 90, 115, 150, 153]

# For each question, let's print all blocks around it on the page and on next column/page if needed
for q in held_qs:
    spec = ch9_skel[q]
    pno = spec["page"]
    page = doc[pno - 1]
    k = ch9_key.get(str(q), {})
    col = spec.get("column")
    
    print("=" * 80)
    print(f"Q{q} | Page {pno} (Col {col}) | Skeleton type: {spec.get('answer_type')} | Key: {k}")
    print(f"Bbox: {spec['bbox']}")
    print("=" * 80)
    
    # Search for Q{q}. on page
    blocks = page.get_text("blocks")
    # sort blocks by y0
    blocks_sorted = sorted(blocks, key=lambda b: (b[1], b[0]))
    
    # Find blocks for this question
    # A block belongs to Q{q} if it's after Q{q}. and before Q{q+1}.
    # Let's check text around bbox
    x0, y0, x1, y1 = spec["bbox"]
    # search next q in same column
    same_col = [
        s for s in ch9_skel.values()
        if s["page"] == pno and s.get("column") == col and s["bbox"][1] > y0 + 2
    ]
    if same_col:
        nxt = min(same_col, key=lambda s: s["bbox"][1])
        clip_y1 = nxt["bbox"][1] - 2
    else:
        clip_y1 = page.rect.y1 - 20
        
    clip = pymupdf.Rect(x0 - 5, y0 - 5, x1 + 5, clip_y1 + 5)
    print("--- CLIPPED TEXT ---")
    print(page.get_text("text", clip=clip).strip())
    
    # Check if there are options or continuation in next column / page
    if not same_col:
        # Check top of next column or page
        if col == "L":
            cont_clip = pymupdf.Rect(300, 30, 580, 150)
            print("--- CONT NEXT COL ---")
            print(page.get_text("text", clip=cont_clip).strip())
        elif col == "R" and pno < doc.page_count:
            nxt_page = doc[pno]
            cont_clip = pymupdf.Rect(35, 30, 300, 150)
            print("--- CONT NEXT PAGE ---")
            print(nxt_page.get_text("text", clip=cont_clip).strip())
