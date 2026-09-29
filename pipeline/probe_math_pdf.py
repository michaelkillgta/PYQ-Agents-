#!/usr/bin/env python3
"""Read-only reconnaissance of the MathonGo Mathematics PYQ PDF. Does not write figures."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf

PDF = Path(r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")
OUT = Path(r"c:\Users\tempo\Downloads\files\math-probe.json")

CHAP_RE = re.compile(r"^CHAPTER\s+(\d+)$")
Q_ANCHOR = re.compile(r"^Q(\d+)\s*([\.\*\^])")
DATE_RE = re.compile(r"(\d{1,2})\s+([A-Z][a-z]{2})\s+(20\d{2})\s*\(([MEF])\)")
CHAPTER_TITLE_LINE = re.compile(r"^\s*(\d{1,2})\.\s+(.+?)\s*$")
TOKEN_RE = re.compile(r"Q(\d+)\s*\(([^)]+)\)")
TIER_NAMES = ("MUST DO", "CONCEPT BUILDER", "ADVANCED")


def line_text(line):
    return "".join(s["text"] for s in line["spans"]).strip()


def main():
    doc = pymupdf.open(PDF)
    n = len(doc)
    p0 = doc[0]
    report = {
        "file": str(PDF),
        "bytes": PDF.stat().st_size,
        "pages": n,
        "page0_size": [round(p0.rect.width, 1), round(p0.rect.height, 1)],
        "is_pdf": True,
    }

    # Cover / TOC / last pages (plain text)
    toc_pages = []
    for i in range(min(8, n)):
        toc_pages.append({"page": i + 1, "text": doc[i].get_text()[:2500]})
    report["front_matter"] = toc_pages

    back = []
    for i in range(max(0, n - 12), n):
        t = doc[i].get_text()
        back.append({
            "page": i + 1,
            "chars": len(t),
            "has_answer_key": "Answer Key" in t or "ANSWER KEY" in t.upper(),
            "preview": t[:1800],
        })
    report["back_matter"] = back

    # Find answer-key start
    ak_start = None
    for i in range(n - 1, -1, -1):
        t = doc[i].get_text()
        if "Answer Key" in t or "ANSWER KEY" in t:
            ak_start = i
        elif ak_start is not None and i < ak_start - 1:
            # keep scanning a bit in case header is on earlier key pages
            pass
    # Walk forward from first "Answer Key" in last 40 pages
    ak_first = None
    for i in range(max(0, n - 40), n):
        if "Answer Key" in doc[i].get_text() or "ANSWER KEY" in doc[i].get_text().upper():
            ak_first = i
            break
    report["answer_key_first_page"] = None if ak_first is None else ak_first + 1

    fonts = Counter()
    chapter_heads = []
    q_count = 0
    q_by_page = []
    dates = 0
    dates_unmatched_shift = 0
    tier_hits = Counter()
    topic_font_samples = []
    drawings_pages = 0
    drawing_items = 0
    image_items = 0
    watermarkish = 0
    vector_pages = []
    chapter_title_by_no = {}
    current_ch = None
    q_per_chapter_guess = Counter()
    text_layer_empty = 0

    for pno in range(n):
        page = doc[pno]
        raw = page.get_text()
        if not raw.strip():
            text_layer_empty += 1
        dates += len(DATE_RE.findall(raw))
        for m in re.finditer(r"(\d{1,2})\s+([A-Z][a-z]{2})\s+(20\d{2})\s*\(([^)]+)\)", raw):
            if m.group(4) not in {"M", "E", "F"}:
                dates_unmatched_shift += 1

        dlist = page.get_drawings()
        if dlist:
            drawings_pages += 1
            drawing_items += len(dlist)
            if len(vector_pages) < 15:
                vector_pages.append({"page": pno + 1, "drawings": len(dlist)})

        for info in page.get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            w, h = x1 - x0, y1 - y0
            pw, ph = page.rect.width, page.rect.height
            if w > 0.85 * pw and h > 0.85 * ph:
                watermarkish += 1
                continue
            if w >= 18 and h >= 18:
                image_items += 1

        page_qs = 0
        d = page.get_text("dict")
        for block in d["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                txt = line_text(line)
                if not txt:
                    continue
                span = line["spans"][0]
                font, size = span["font"], round(span["size"], 2)
                fonts[f"{font}@{size}"] += 1

                m = CHAP_RE.match(txt)
                if m and size > 15:
                    current_ch = int(m.group(1))
                    chapter_heads.append({
                        "page": pno + 1,
                        "chapter_no": current_ch,
                        "font": font,
                        "size": size,
                    })
                    continue

                # title after CHAPTER N — large extra-bold nearby
                if current_ch and current_ch not in chapter_title_by_no and size > 28:
                    if font.lower().find("fira") >= 0 or font.lower().find("bold") >= 0:
                        chapter_title_by_no[current_ch] = {
                            "title": txt,
                            "page": pno + 1,
                            "font": font,
                            "size": size,
                        }

                up = txt.upper()
                for tname in TIER_NAMES:
                    if up.startswith(tname) and 9 < size < 14:
                        tier_hits[tname] += 1
                        if len(topic_font_samples) < 12 and tname == "MUST DO":
                            topic_font_samples.append({
                                "kind": "tier",
                                "text": txt,
                                "font": font,
                                "size": size,
                                "page": pno + 1,
                            })

                if "TimesNewRoman" in font and 10 < size < 13 and len(txt) > 3:
                    if len(topic_font_samples) < 30:
                        topic_font_samples.append({
                            "kind": "topic_candidate",
                            "text": txt[:80],
                            "font": font,
                            "size": size,
                            "page": pno + 1,
                        })

                if Q_ANCHOR.match(txt):
                    q_count += 1
                    page_qs += 1
                    if current_ch:
                        q_per_chapter_guess[current_ch] += 1

        if page_qs:
            q_by_page.append({"page": pno + 1, "q_anchors": page_qs})

    report["text_layer_empty_pages"] = text_layer_empty
    report["fonts_top"] = fonts.most_common(25)
    report["chapter_heads"] = chapter_heads
    report["chapter_titles"] = chapter_title_by_no
    report["q_anchor_count"] = q_count
    report["q_pages"] = len(q_by_page)
    report["q_per_chapter_running"] = dict(sorted(q_per_chapter_guess.items()))
    report["tier_hits"] = dict(tier_hits)
    report["date_hits"] = dates
    report["image_objects_ge_18pt"] = image_items
    report["watermarkish_fullpage_images"] = watermarkish
    report["pages_with_vector_drawings"] = drawings_pages
    report["vector_drawing_items"] = drawing_items
    report["vector_pages_sample"] = vector_pages
    report["topic_font_samples"] = topic_font_samples[:20]

    # Answer key parse (same regex as Physics)
    if ak_first is not None:
        text = ""
        for pno in range(ak_first, n):
            text += doc[pno].get_text()
        marks = [(m.start(), int(m.group(1)), m.group(2).strip())
                 for m in re.finditer(r"^\s*(\d{1,2})\.\s+([A-Z][A-Za-z0-9 ,\-&'/]+?)\s*$", text, re.M)]
        key = {}
        for i, (pos, num, title) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
            answers = {}
            for q, a in TOKEN_RE.findall(text[pos:end]):
                a = a.strip()
                answers[int(q)] = {
                    "type": "mcq" if a in {"1", "2", "3", "4"} else "numerical",
                    "value": a,
                }
            key[num] = {"chapter_no": num, "title": title, "n": len(answers),
                        "mcq": sum(1 for v in answers.values() if v["type"] == "mcq"),
                        "numerical": sum(1 for v in answers.values() if v["type"] == "numerical")}
        report["answer_key_chapters"] = key
        report["answer_key_chapter_count"] = len(key)
        report["answer_key_total"] = sum(c["n"] for c in key.values())
        report["answer_key_mcq"] = sum(c["mcq"] for c in key.values())
        report["answer_key_numerical"] = sum(c["numerical"] for c in key.values())
        report["answer_key_raw_head_sample"] = text[:1500]
    else:
        report["answer_key_chapters"] = {}

    # Sample a mid content page for math glyphs
    sample_pno = min(40, n - 1)
    report["sample_page"] = {
        "page": sample_pno + 1,
        "text": doc[sample_pno].get_text()[:2200],
    }

    # First chapter-start page text
    if chapter_heads:
        p = chapter_heads[0]["page"] - 1
        report["first_chapter_page_text"] = doc[p].get_text()[:1800]

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"pages={n} q_anchors={q_count} chapters_heads={len(chapter_heads)}")
    print(f"ak_page={report.get('answer_key_first_page')} ak_ch={report.get('answer_key_chapter_count')} ak_n={report.get('answer_key_total')}")
    print(f"images={image_items} drawings_pages={drawings_pages} drawing_items={drawing_items}")
    print(f"tiers={dict(tier_hits)} dates={dates} empty_text={text_layer_empty}")
    print("chapter titles:")
    for k in sorted(chapter_title_by_no):
        print(f"  {k:2d}. {chapter_title_by_no[k]['title']}  (p{chapter_title_by_no[k]['page']})")
    if report.get("answer_key_chapters"):
        print("answer key:")
        for num, c in sorted(report["answer_key_chapters"].items(), key=lambda x: int(x[0])):
            print(f"  {int(num):2d}. {c['title']}  n={c['n']} mcq={c['mcq']} num={c['numerical']}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
