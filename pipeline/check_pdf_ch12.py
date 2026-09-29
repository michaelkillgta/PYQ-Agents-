import fitz # PyMuPDF
import json

doc = fitz.open(r"c:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")
print("PDF opened, total pages:", len(doc))

ch12_pages = list(range(113, 120)) # 114 to 120 (1-based)
for pno in ch12_pages:
    page = doc[pno]
    text = page.get_text()
    print(f"=== Page {pno + 1} (chars {len(text)}) ===")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    print("First 2 lines:", lines[:2])
    print("Last 2 lines:", lines[-2:])

doc.close()
