#!/usr/bin/env python3
"""Read-only probe of every Definite Integration source PDF."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pymupdf

PDFS = [
    Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2026 (Jan) - MathonGo.pdf"),
    Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 April Chapter-wise Question Bank - MathonGo.pdf"),
    Path(r"C:\Users\tempo\Downloads\Mathematics - JEE Main 2025 January Chapter-wise Question Bank - MathonGo.pdf"),
    Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 January Question Bank - MathonGo.pdf"),
    Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2024 April Question Bank - MathonGo.pdf"),
    Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 April Chapterwise PYQ - MathonGo.pdf"),
    Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2023 January Chapter wise Questions by MathonGo.pdf"),
    Path(r"C:\Users\tempo\Downloads\Definite Integration - JEE Main 2022 Chapter wise Questions by MathonGo.pdf"),
    Path(r"C:\Users\tempo\Downloads\Definite Integration.pdf"),
    Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_march_chapterwise_JhLuivAhhuEbSCISHMto.pdf"),
    Path(r"C:\Users\tempo\Downloads\mathongo_question_definite_integration_jee_main_2021_february_chapterwiseW7xhGEpjPf0BnZlSz5TE.pdf"),
    Path(r"C:\Users\tempo\Downloads\cqb_jm_jan_2020_math_definite_integration.pdf"),
    Path(r"C:\Users\tempo\Downloads\definite_integration_questions_jee_main_2020_chapterwise_question_bank_mathongo.pdf"),
]

Q_RE = re.compile(r"\bQ\s*(\d+)\s*[.\)]")
DATE_RE = re.compile(
    r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(20\d{2})",
    re.I,
)
YEAR_RE = re.compile(r"\b(20(?:1[9]|2[0-6]))\b")
CHAPTER_RE = re.compile(r"CHAPTER\s+(\d+)|^\s*(\d{1,2})\.\s+Definite Integration", re.I)
DI_RE = re.compile(r"Definite Integration", re.I)
AK_RE = re.compile(r"Answer Key|ANSWER KEY|Answer Keys", re.I)
MONTH_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
    re.I,
)


def preview(text: str, n: int = 900) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\n", " | "))[:n]


def main() -> None:
    reports = []
    for pdf in PDFS:
        item = {
            "exists": pdf.exists(),
            "name": pdf.name,
            "path": str(pdf),
        }
        if not pdf.exists():
            reports.append(item)
            continue
        item["bytes"] = pdf.stat().st_size
        doc = pymupdf.open(pdf)
        n = len(doc)
        item["pages"] = n
        q_nos: list[int] = []
        dates: list[str] = []
        months: Counter[str] = Counter()
        years: Counter[str] = Counter()
        di_pages: list[int] = []
        ak_pages: list[int] = []
        chapter_hits: list[str] = []
        page_previews = []
        for i, page in enumerate(doc):
            text = page.get_text() or ""
            pno = i + 1
            if DI_RE.search(text):
                di_pages.append(pno)
            if AK_RE.search(text):
                ak_pages.append(pno)
            for m in Q_RE.finditer(text):
                q_nos.append(int(m.group(1)))
            for m in DATE_RE.finditer(text):
                dates.append(f"{m.group(1)} {m.group(2)} {m.group(3)}")
            for m in MONTH_RE.finditer(text):
                months[m.group(1).title()] += 1
            for m in YEAR_RE.finditer(text):
                years[m.group(1)] += 1
            for m in CHAPTER_RE.finditer(text):
                chapter_hits.append(f"p{pno}:{m.group(0)[:60]}")
            if pno <= 3 or pno == n or (ak_pages and pno == ak_pages[0]):
                page_previews.append({"page": pno, "preview": preview(text)})
        item["q_min"] = min(q_nos) if q_nos else None
        item["q_max"] = max(q_nos) if q_nos else None
        item["q_unique"] = sorted(set(q_nos))[:40]
        item["q_unique_count"] = len(set(q_nos))
        item["q_anchor_hits"] = len(q_nos)
        item["dates_sample"] = dates[:20]
        item["date_count"] = len(dates)
        item["months"] = dict(months.most_common(8))
        item["years"] = dict(years.most_common(8))
        item["di_pages"] = di_pages[:30]
        item["di_page_count"] = len(di_pages)
        item["ak_pages"] = ak_pages[:20]
        item["chapter_hits"] = chapter_hits[:20]
        item["previews"] = page_previews
        # For fat books, find first/last DI-heavy stretch
        if n > 40:
            di_only = [p for p in di_pages]
            item["di_page_span"] = [di_only[0], di_only[-1]] if di_only else None
        doc.close()
        reports.append(item)
        print(f"OK {pdf.name} pages={n} q_unique={item['q_unique_count']} qmax={item['q_max']} years={item['years']}", flush=True)

    out = Path(r"c:\Users\tempo\Downloads\files\out-di-yearbooks\probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
