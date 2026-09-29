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
ch8_skel = {s["q_no"]: s for s in skel if s.get("chapter_no") == 8}
ch8_key = key_book.get("8", {}).get("answers", {})

held_qs = [17, 30, 31, 38, 45, 50, 57, 60, 73, 74, 76, 91, 93, 95, 96, 103, 105, 107]

for q in held_qs:
    spec = ch8_skel[q]
    pno = spec["page"]
    page = doc[pno - 1]
    k = ch8_key.get(str(q), {})
    
    print("=" * 80)
    print(f"Q{q} | Page: {pno} | Skeleton Type: {spec.get('answer_type')} | Key: {k}")
    print(f"Bbox: {spec['bbox']}, Col: {spec.get('column')}")
    print("=" * 80)
    
    # Extract words/blocks in the vicinity
    # First, let's find all text blocks on the page in reading order
    blocks = page.get_text("blocks")
    # sort blocks by x, y or find the block containing Q{q}.
    relevant = []
    for b in blocks:
        text = b[4]
        if f"Q{q}." in text or f"Q{q} " in text or f"Q {q}" in text:
            relevant.append(text)
    
    if relevant:
        print("MATCHED BLOCKS:")
        for r in relevant:
            print(r.strip())
    else:
        print("NO DIRECT BLOCK MATCH. Let's inspect text around bbox:")
        x0, y0, x1, y1 = spec["bbox"]
        # expand bbox slightly
        clip = pymupdf.Rect(x0 - 5, y0 - 5, x1 + 5, y1 + 50)
        print(page.get_text("text", clip=clip).strip())
