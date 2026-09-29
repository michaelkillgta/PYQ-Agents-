"""List every PDF image xref inside 2024 Jan/Apr DI solution crops."""
from __future__ import annotations

import json
from pathlib import Path

import pymupdf

from ingest_math_2025_paper_solutions import crop_rect, WATERMARK_COVERAGE

BOOKS = [
    {
        "id": "2024-jan",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 January Question Bank - MathonGo.pdf"),
        "inv": Path(r"c:\Users\tempo\Downloads\files\out-math-2024-jan-di-solutions\inventory.json"),
        "packets": Path(r"c:\Users\tempo\Downloads\files\out-math-2024-jan-di-solutions\packets.json"),
    },
    {
        "id": "2024-apr",
        "pdf": Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 April Question Bank - MathonGo.pdf"),
        "inv": Path(r"c:\Users\tempo\Downloads\files\out-math-2024-apr-di-solutions\inventory.json"),
        "packets": Path(r"c:\Users\tempo\Downloads\files\out-math-2024-apr-di-solutions\packets.json"),
    },
]
MIN_PT = 20


def hits_for(doc, spec: dict) -> list[dict]:
    pages = [(spec["page"], spec)]
    cont = spec.get("continuation")
    if spec.get("continues") and cont:
        pages.append((cont["page"], None))
    found = []
    for page_no, local in pages:
        page = doc[page_no - 1]
        pw, ph = page.rect.width, page.rect.height
        clip = (
            crop_rect(page, local)
            if local
            else pymupdf.Rect(
                page.rect.x0,
                page.rect.y0 + 40,
                page.rect.x1,
                float(cont.get("cut_y") or page.rect.y0 + 220) - 4,
            )
        )
        for info in page.get_image_info(xrefs=True):
            bbox = pymupdf.Rect(info["bbox"])
            w, h = bbox.width, bbox.height
            if w > WATERMARK_COVERAGE * pw and h > WATERMARK_COVERAGE * ph:
                continue
            hit = bbox & clip
            if hit.is_empty or hit.width < MIN_PT or hit.height < MIN_PT:
                continue
            found.append(
                {
                    "page": page_no,
                    "xref": int(info["xref"]),
                    "w": round(w, 1),
                    "h": round(h, 1),
                    "y0": round(bbox.y0, 1),
                    "x0": round(bbox.x0, 1),
                }
            )
    found.sort(key=lambda r: (r["page"], r["y0"], r["x0"]))
    return found


def main() -> None:
    rows = []
    for book in BOOKS:
        report = json.loads(book["inv"].read_text(encoding="utf-8"))
        packets = {int(p["pdf_q"]): p for p in json.loads(book["packets"].read_text(encoding="utf-8"))}
        doc = pymupdf.open(book["pdf"])
        try:
            for spec in report["chapters"][0]["crop_plan"]:
                q = int(spec["q_no"])
                hits = hits_for(doc, spec)
                md = str((packets.get(q) or {}).get("solution_md") or "")
                tokens = md.count("[[fig:")
                rows.append(
                    {
                        "book": book["id"],
                        "q": q,
                        "xrefs": len(hits),
                        "tokens": tokens,
                        "hits": hits,
                    }
                )
        finally:
            doc.close()
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
