#!/usr/bin/env python3
"""Extract Q headers, dates, and answer keys from every DI source PDF."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf

PDFS = [
    ("2026-jan", Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2026 (Jan) - MathonGo.pdf")),
    ("2025-apr-book", Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf")),
    ("2025-jan-book", Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf")),
    ("2024-jan", Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 January Question Bank - MathonGo.pdf")),
    ("2024-apr", Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 April Question Bank - MathonGo.pdf")),
    ("2023-apr", Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 April Chapterwise PYQ - MathonGo.pdf")),
    ("2023-jan", Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 January Chapter wise Questions by MathonGo.pdf")),
    ("2022-jun", Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2022 Chapter wise Questions by MathonGo.pdf")),
    ("2022-other", Path(r"C:\Users\tempo\Downloads\Definite Integration.pdf")),
    ("2021-mar", Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_march_chapterwise_JhLuivAhhuEbSCISHMto.pdf")),
    ("2021-feb", Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_february_chapterwiseW7xhGEpjPf0BnZlSz5TE.pdf")),
    ("2020-jan", Path(r"C:\Users\tempo\Downloads\cqb_jm_jan_2020_math_definite_integration.pdf")),
    ("2020-other", Path(r"C:\Users\tempo\Downloads\definite_integration_questions_jee_main_2020_chapterwise_question_bank_mathongo.pdf")),
]

HEADS = [
    re.compile(r"Q(\d+)\.\s*JEE Main 20(\d{2})\s*\((\d{1,2})\s+([A-Za-z]+)\s+Shift\s+([12])\)", re.I),
    re.compile(r"Q(\d+)\s*[-–]\s*20(\d{2})\s*\((\d{1,2})\s+([A-Za-z]+)\s+Shift\s+([12])\)", re.I),
    re.compile(r"Q(\d+)\s*[-–]\s*(\d{1,2})\s+([A-Za-z]+)\s*[-–]\s*Shift\s+([12])", re.I),
    re.compile(r"\[20(\d{2})\s*\((\d{1,2})\s+([A-Za-z]+)\s+Shift\s+([12])\)\]", re.I),
]
NUM_HEAD = re.compile(r"(?:^|\n)\s*(\d{1,2})\.\s")
KEY_LINE = re.compile(
    r"(?:Q\s*)?(\d{1,2})\s*[\.\)]\s*(?:\(([0-9A-D]+)\)|([0-9A-D]+))",
    re.I,
)
MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def dump_pages(doc, pages: list[int], nchars: int = 2500):
    out = []
    for pno in pages:
        if pno < 1 or pno > len(doc):
            continue
        text = doc[pno - 1].get_text() or ""
        out.append({"page": pno, "text": text[:nchars]})
    return out


def main() -> None:
    reports = []
    for key, pdf in PDFS:
        doc = pymupdf.open(pdf)
        n = len(doc)
        headers = []
        full = []
        for i, page in enumerate(doc):
            text = page.get_text() or ""
            full.append(text)
            for rx in HEADS:
                for m in rx.finditer(text):
                    headers.append({"page": i + 1, "raw": m.group(0), "groups": list(m.groups())})
        joined = "\n".join(full)
        keys = []
        in_key = False
        for i, text in enumerate(full):
            if re.search(r"Answer Key|ANSWER KEY|ANSWERS AND SOLUTIONS", text, re.I):
                in_key = True
            if in_key:
                for m in KEY_LINE.finditer(text):
                    keys.append({"page": i + 1, "q": int(m.group(1)), "val": m.group(2) or m.group(3)})
                # stop after first solutions dump that isn't the key table
                if i > 0 and "Q1" not in text[:200] and len(keys) >= 8:
                    # keep scanning a bit
                    pass
        item = {
            "id": key,
            "pages": n,
            "header_count": len(headers),
            "headers": headers,
            "key_hits": keys[:40],
            "key_count": len(keys),
        }
        if n > 40:
            # dump TOC + suspected DI pages
            item["toc"] = dump_pages(doc, [2, 3], 2000)
            if key == "2025-apr-book":
                item["di_q"] = dump_pages(doc, [36, 37, 38, 39], 3500)
                item["di_key"] = dump_pages(doc, [64, 65], 2500)
            elif key == "2025-jan-book":
                item["di_q"] = dump_pages(doc, [36, 37, 38, 39, 40], 3500)
                item["di_key"] = dump_pages(doc, [67, 68], 2500)
        else:
            item["first"] = dump_pages(doc, [1, 2, 3], 1800)
            # last question page before solutions often around mid
            item["mid"] = dump_pages(doc, [max(1, n // 3), max(1, n // 2)], 1200)
        doc.close()
        reports.append(item)
        print(f"{key}: pages={n} headers={len(headers)} keys={len(keys)}", flush=True)

    out = Path(r"c:\Users\tempo\Downloads\files\out-di-yearbooks\headers.json")
    out.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
