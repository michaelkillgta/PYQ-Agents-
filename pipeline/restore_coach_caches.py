#!/usr/bin/env python3
"""Restore coach JSON from pyq-coach + di-coach caches; flag formfeed corruption."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import generate_di_coach as di
import pyq_common as p

CACHES = [
    Path(r"c:\Users\tempo\Downloads\files\out-math-pyq-coach\glm"),
    Path(r"c:\Users\tempo\Downloads\files\out-math-di-coach\glm"),
]
SLUGS = [
    "basic-of-mathematics",
    "complex-number",
    "binomial-theorem",
    "determinants",
    "continuity-and-differentiability",
    "application-of-derivatives",
    "definite-integration",
    "area-under-curves",
    "differential-equations",
    "circle",
]


def math_chapters(sb):
    sid = sb.table("pyq_subjects").select("id").eq("name", "Mathematics").execute().data[0]["id"]
    units = [u["id"] for u in sb.table("pyq_units").select("id").eq("subject_id", sid).execute().data]
    return (
        sb.table("pyq_chapters")
        .select("id,chapter_no,catalog_slug")
        .in_("unit_id", units)
        .in_("catalog_slug", SLUGS)
        .execute()
        .data
        or []
    )


def fetch_all(sb, chapter_id: str) -> list[dict]:
    out = []
    start = 0
    while True:
        chunk = (
            sb.table("pyq_questions")
            .select("id,q_no,review_status,tips_md,formulas_md,solution_md")
            .eq("chapter_id", chapter_id)
            .range(start, start + 999)
            .execute()
            .data
            or []
        )
        out.extend(chunk)
        if len(chunk) < 1000:
            break
        start += 1000
    return out


def parse_json(raw: str):
    s = (raw or "").strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def corrupted(obj) -> bool:
    blob = json.dumps(obj, ensure_ascii=False) if obj is not None else ""
    if "\x0c" in blob or "\x08" in blob:
        return True
    if "rac{" in blob and "\\frac" not in str(obj):
        return True
    return False


def from_caches(qid: str):
    for root in CACHES:
        path = root / f"{qid}.json"
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        parsed = di.validate(data)
        if parsed:
            return parsed
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sb = p.supabase_client()
    restored = 0
    still = []
    for ch in sorted(math_chapters(sb), key=lambda r: int(r["chapter_no"])):
        live = [r for r in fetch_all(sb, ch["id"]) if r.get("review_status") in {"auto_ok", "human_ok"}]
        n_bad = 0
        for row in live:
            tips = parse_json(row.get("tips_md") or "")
            forms = parse_json(row.get("formulas_md") or "")
            bad = tips is None or forms is None or corrupted(tips) or corrupted(forms)
            if not bad:
                parsed = di.validate({"tips": (tips or {}).get("tips"), "formulas": (forms or {}).get("formulas")})
                if parsed:
                    continue
                bad = True
            n_bad += 1
            parsed = from_caches(row["id"])
            if not parsed:
                still.append(row["id"])
                continue
            tips_l, formulas = parsed
            sb.table("pyq_questions").update(
                {
                    "tips_md": json.dumps({"tips": tips_l}, ensure_ascii=False),
                    "formulas_md": json.dumps({"formulas": formulas}, ensure_ascii=False),
                }
            ).eq("id", row["id"]).execute()
            restored += 1
        print(f"ch{ch['chapter_no']} live={len(live)} repaired_this_pass need={n_bad}", flush=True)
    print(f"restored={restored} still={len(still)}", flush=True)
    Path(r"c:\Users\tempo\Downloads\files\out-math-named\coach_still.json").write_text(
        json.dumps(still, indent=1), encoding="utf-8"
    )
    for qid in still:
        print(qid, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
