#!/usr/bin/env python3
"""Compare live Maths DB keys to the PDF answer key. No Sarvam.

    python audit_math_pdf_keys.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import pyq_common as p

p.configure_book("math")


def fetch_rows(sb, chapter_id: str) -> list[dict]:
    out: list[dict] = []
    start = 0
    while True:
        chunk = (
            sb.table("pyq_questions")
            .select("q_no,format,correct_option,numerical_answer,review_status")
            .eq("chapter_id", chapter_id)
            .order("q_no")
            .range(start, start + 999)
            .execute()
            .data
        )
        if not chunk:
            break
        out.extend(chunk)
        if len(chunk) < 1000:
            break
        start += 1000
    return out


def main() -> int:
    key_book = p.load_answer_key()
    sb = p.supabase_client()
    chapters = (
        sb.table("pyq_chapters")
        .select("id,chapter_no,name")
        .eq("unit_id", 3)
        .order("chapter_no")
        .execute()
        .data
    )
    mismatches = []
    scanned = 0
    for ch in chapters:
        rows = fetch_rows(sb, ch["id"])
        answers = (key_book.get(str(ch["chapter_no"])) or {}).get("answers") or {}
        for r in rows:
            scanned += 1
            q = int(r["q_no"])
            k = answers.get(str(q))
            if not k:
                mismatches.append({
                    "chapter_no": ch["chapter_no"],
                    "q_no": q,
                    "reason": "missing_pdf_key",
                })
                continue
            ktype = k.get("type")
            kval = str(k.get("value") or "").strip()
            fmt = r.get("format")
            if ktype == "mcq":
                db = r.get("correct_option")
                if fmt != "mcq" or str(db) != kval:
                    mismatches.append({
                        "chapter_no": ch["chapter_no"],
                        "name": ch["name"],
                        "q_no": q,
                        "reason": "key_mismatch",
                        "pdf": f"{ktype}:{kval}",
                        "db": f"{fmt}:{db}",
                    })
            else:
                db = str(r.get("numerical_answer") or "").strip()
                if fmt != "numerical" or db != kval:
                    mismatches.append({
                        "chapter_no": ch["chapter_no"],
                        "name": ch["name"],
                        "q_no": q,
                        "reason": "key_mismatch",
                        "pdf": f"{ktype}:{kval}",
                        "db": f"{fmt}:{db}",
                    })
    dest = Path("out-math/glm_option_audit/pdf_key_vs_db.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(mismatches, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"scanned {scanned}")
    print(f"pdf-key mismatches {len(mismatches)}")
    for row in mismatches[:40]:
        print(f"  ch{row['chapter_no']} Q{row['q_no']} {row['reason']} pdf={row.get('pdf')} db={row.get('db')}")
    if len(mismatches) > 40:
        print(f"  … {len(mismatches) - 40} more")
    print(f"wrote {dest}")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
