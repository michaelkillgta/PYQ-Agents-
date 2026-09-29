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

# Load OCR files
pages_needed = sorted(set(ch8_skel[q]["page"] for q in held_qs))
ocr_pages = {}
for p in pages_needed:
    with open(f"out-math/ocr/page_{p:03d}.json", "r", encoding="utf-8") as f:
        ocr_pages[p] = json.load(f)

# Load parsed.json, gemma4.json, glm53_flash.json
with open("out-math/agents/chapter_8/parsed.json", "r", encoding="utf-8") as f:
    parsed = json.load(f)
with open("out-math/agents/chapter_8/gemma4.json", "r", encoding="utf-8") as f:
    gemma4 = json.load(f)
with open("out-math/agents/chapter_8/glm53_flash.json", "r", encoding="utf-8") as f:
    glm53 = json.load(f)

for q in held_qs:
    spec = ch8_skel[q]
    pno = spec["page"]
    k = ch8_key.get(str(q), {})
    
    print("=" * 80)
    print(f"QUESTION Q{q} (Page {pno}) | Key: {k} | Type: {spec.get('answer_type')}")
    print("=" * 80)
    
    # Check text in PDF bounding box or nearby
    page = doc[pno - 1]
    # Extract text from page around Q{q}.
    page_text = page.get_text("text")
    # find where Q{q}. starts
    start_idx = page_text.find(f"Q{q}.")
    if start_idx != -1:
        # find next Q{q+1}.
        end_idx = page_text.find(f"Q{q+1}.", start_idx)
        if end_idx == -1:
            snippet = page_text[start_idx:start_idx + 800]
        else:
            snippet = page_text[start_idx:end_idx]
        print("--- RAW PDF TEXT ---")
        print(snippet.strip())
    else:
        print("--- RAW PDF TEXT: Not found by simple search ---")
        
    print("\n--- PARSED.JSON ---")
    print(json.dumps(parsed.get(str(q)), ensure_ascii=False, indent=2))
    
    print("\n--- GEMMA4 ---")
    print(json.dumps(gemma4.get(str(q)), ensure_ascii=False, indent=2))
    
    print("\n--- GLM53_FLASH ---")
    print(json.dumps(glm53.get(str(q)), ensure_ascii=False, indent=2))
