#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import generate_di_coach as di
import pyq_common as p

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


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sb = p.supabase_client()
    sid = sb.table("pyq_subjects").select("id").eq("name", "Mathematics").execute().data[0]["id"]
    units = [u["id"] for u in sb.table("pyq_units").select("id").eq("subject_id", sid).execute().data]
    chapters = (
        sb.table("pyq_chapters")
        .select("id,chapter_no,catalog_slug")
        .in_("unit_id", units)
        .in_("catalog_slug", SLUGS)
        .execute()
        .data
        or []
    )
    tot_live = tot_sol = tot_coach = tot_held = 0
    for ch in sorted(chapters, key=lambda r: int(r["chapter_no"])):
        rows = []
        start = 0
        while True:
            chunk = (
                sb.table("pyq_questions")
                .select("id,q_no,review_status,body,solution_md,tips_md,formulas_md")
                .eq("chapter_id", ch["id"])
                .range(start, start + 999)
                .execute()
                .data
                or []
            )
            rows.extend(chunk)
            if len(chunk) < 1000:
                break
            start += 1000
        live = [r for r in rows if r.get("review_status") in {"auto_ok", "human_ok"}]
        held = len(rows) - len(live)
        empty_sol = []
        bad_coach = []
        for r in live:
            if not (r.get("solution_md") or "").strip():
                empty_sol.append(r["q_no"])
            tips = r.get("tips_md") or ""
            forms = r.get("formulas_md") or ""
            ok = False
            try:
                t = json.loads(tips)
                f = json.loads(forms)
                parsed = di.validate({"tips": t.get("tips"), "formulas": f.get("formulas")})
                ok = parsed is not None and "\x0c" not in tips and "\x0c" not in forms
            except Exception:
                ok = False
            if not ok:
                bad_coach.append(r["q_no"])
        tot_live += len(live)
        tot_sol += len(live) - len(empty_sol)
        tot_coach += len(live) - len(bad_coach)
        tot_held += held
        print(
            f"ch{ch['chapter_no']} live={len(live)} held={held} empty_sol={empty_sol} bad_coach={bad_coach}",
            flush=True,
        )
    print(f"TOTAL live={tot_live} sol={tot_sol} coach={tot_coach} held={tot_held}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
