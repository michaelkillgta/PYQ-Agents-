#!/usr/bin/env python3
"""Audit every stem/option in a parsed chapter for paper-only violations.

Run after extract_ocr / write_and_publish. Exit 1 if anything remains.

    python audit_paper_text.py
    python audit_paper_text.py --parsed out/extracted/pass1/parsed.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CAPTION = re.compile(
    r"(The image\s+(?:displays|shows|is)\b|"
    r"Note:\s*The function is not explicitly|"
    r"It does not contain any charts|"
    r"The diagram (?:features|illustrates|visually)|"
    r"This image is|"
    r"schematic diagram|"
    r"data chart or graph)",
    re.I,
)
STARS = re.compile(r"\*\*")
TABLE = re.compile(r"<table\b|\| :---", re.I)
WATERMARK = re.compile(
    r"#\s*PaperPhodnaHai|www\.mathongo\.com|\bmathongo\b|"
    r"\s+#\s*#\s*mi\s*$|\s+\d{1,3}(?:\s+\d{1,3})+\s+mi\s*$",
    re.I,
)
HEADING = re.compile(
    r"MUST DO PROBLEMS|ADVANCED STYLE PROBLEMS|CONCEPT BUILDER|Spring force|"
    r"Frictional force|Non-uniform Circular Motion|Power of iota|"
    r"Algebra of complex numbers|Geometry of Complex Number|"
    r"Locus Based on Distance Formula",
    re.I,
)
EMPTYISH = re.compile(r"^(√|N|\*|(?:4[6-9]|5[0-9]|60)|)$")
LONG_OPTION = 180


def flags_for(text: str, *, is_option: bool) -> list[str]:
    s = (text or "").strip()
    out = []
    if CAPTION.search(s):
        out.append("caption")
    if STARS.search(s):
        out.append("stars")
    if TABLE.search(s):
        out.append("table")
    if WATERMARK.search(s):
        out.append("watermark")
    if HEADING.search(s):
        out.append("heading")
    if is_option and len(s) > LONG_OPTION:
        out.append(f"long_option:{len(s)}")
    if is_option and EMPTYISH.fullmatch(s):
        out.append("empty_or_page")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--parsed",
        default=str(ROOT / "out" / "extracted" / "pass1" / "parsed.json"),
    )
    args = ap.parse_args()
    parsed = json.loads(Path(args.parsed).read_text(encoding="utf-8"))

    def sort_key(kv):
        k = str(kv[0])
        if ":" in k:
            a, b = k.split(":", 1)
            return (int(a), int(b))
        return (0, int(k))

    hits = []
    for q_no, entry in sorted(parsed.items(), key=sort_key):
        label = str(q_no)
        body = entry.get("body") or ""
        bf = flags_for(body, is_option=False)
        if bf:
            hits.append((label, "body", bf, body[:160]))
        opts = entry.get("options")
        if isinstance(opts, list):
            for i, opt in enumerate(opts, start=1):
                of = flags_for(opt, is_option=True)
                if of:
                    hits.append((label, f"opt{i}", of, (opt or "")[:160]))

    blocking = [h for h in hits if any(not f.startswith("empty") for f in h[2])]
    held_shape = [h for h in hits if h not in blocking]
    print(f"questions scanned : {len(parsed)}")
    print(f"blocking          : {len(blocking)}")
    print(f"held-shape (ok)   : {len(held_shape)}")
    by: dict[str, int] = {}
    for _, _, fl, _ in blocking:
        for f in fl:
            by[f.split(":")[0]] = by.get(f.split(":")[0], 0) + 1
    print("blocking flags    :", by or "{}")
    for q, where, fl, preview in blocking[:40]:
        print(f"  Q{q:<8} {where:<6} {','.join(fl)}  {preview!r}")
    if len(blocking) > 40:
        print(f"  … {len(blocking) - 40} more blocking rows")
    if held_shape:
        qs = sorted({h[0] for h in held_shape}, key=lambda x: sort_key((x, None)))
        print("empty/page options (held, not student-visible):", qs[:40],
              f"… +{len(qs)-40}" if len(qs) > 40 else "")
    return 0 if not blocking else 1


if __name__ == "__main__":
    sys.exit(main())
