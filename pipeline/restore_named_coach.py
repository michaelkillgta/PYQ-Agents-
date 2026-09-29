#!/usr/bin/env python3
"""Restore tips_md/formulas_md JSON after accidental \\ collapse. Ping math figure URLs."""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

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
CACHE = Path(r"c:\Users\tempo\Downloads\files\out-math-pyq-coach\glm")
FIG_RE = re.compile(r"\[\[fig:([a-zA-Z0-9_]+)\]\]")
SUBJECT = "Mathematics"


def math_chapters(sb):
    sid = sb.table("pyq_subjects").select("id").eq("name", SUBJECT).execute().data[0]["id"]
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
            .select("id,q_no,review_status,body,solution_md,tips_md,formulas_md")
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


def json_ok(raw: str) -> bool:
    s = (raw or "").strip()
    if not s:
        return False
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False


def from_cache(qid: str):
    path = CACHE / f"{qid}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return di.validate(data)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    env = p.load_env()
    sb = p.supabase_client()
    restored = 0
    broken_no_cache = []
    empty_tips = []
    empty_sol = []
    fig_keys = set()
    smashed_stems = []
    for ch in sorted(math_chapters(sb), key=lambda r: int(r["chapter_no"])):
        rows = fetch_all(sb, ch["id"])
        live = [r for r in rows if r.get("review_status") in {"auto_ok", "human_ok"}]
        print(f"ch{ch['chapter_no']} live={len(live)}", flush=True)
        for row in live:
            body = row.get("body") or ""
            if "\text{" in body.replace("\\text{", "") or "\\\\lim" in body or "\text{" in body:
                if "\t" + "ext{" in body or r"\\lim" in body:
                    smashed_stems.append((ch["chapter_no"], row["q_no"], row["id"][:8]))
            sol = row.get("solution_md") or ""
            if not sol.strip():
                empty_sol.append((ch["chapter_no"], row["q_no"], row["id"]))
            for key in FIG_RE.findall(body + "\n" + sol):
                fig_keys.add(key)
            tips_ok = json_ok(row.get("tips_md") or "")
            forms_ok = json_ok(row.get("formulas_md") or "")
            if tips_ok and forms_ok:
                continue
            parsed = from_cache(row["id"])
            if not parsed:
                if not (row.get("tips_md") or "").strip():
                    empty_tips.append(row["id"])
                else:
                    broken_no_cache.append(row["id"])
                print(f"  NOCACHE ch{ch['chapter_no']} q{row['q_no']} tips_ok={tips_ok} forms_ok={forms_ok}", flush=True)
                continue
            tips, formulas = parsed
            sb.table("pyq_questions").update(
                {
                    "tips_md": json.dumps({"tips": tips}, ensure_ascii=False),
                    "formulas_md": json.dumps({"formulas": formulas}, ensure_ascii=False),
                }
            ).eq("id", row["id"]).execute()
            restored += 1
            print(f"  restored ch{ch['chapter_no']} q{row['q_no']}", flush=True)
    print(
        f"restored={restored} broken_no_cache={len(broken_no_cache)} empty_tips={len(empty_tips)} empty_sol={len(empty_sol)}",
        flush=True,
    )
    print("empty_sol", empty_sol, flush=True)
    print("smashed leftover", smashed_stems[:10], "n", len(smashed_stems), flush=True)

    base = (env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL") or "").rstrip("/")
    urls = {k: f"{base}/storage/v1/object/public/pyq/math/figures/{k}.png" for k in fig_keys}
    print(f"GET {len(urls)} math figure keys", flush=True)
    bad = []

    def ping(item):
        key, url = item
        try:
            r = httpx.get(url, timeout=20.0)
            return key, r.status_code, len(r.content)
        except Exception as exc:
            return key, 0, str(exc)

    with ThreadPoolExecutor(max_workers=16) as pool:
        for key, status, nbytes in pool.map(ping, urls.items()):
            if status != 200 or (isinstance(nbytes, int) and nbytes < 24):
                bad.append({"key": key, "status": status, "bytes": nbytes})
    print(f"bad figures {len(bad)}/{len(urls)}", flush=True)
    for b in bad:
        print(" ", b, flush=True)
    dest = Path(r"c:\Users\tempo\Downloads\files\out-math-named\restore_coach.json")
    dest.write_text(
        json.dumps(
            {
                "restored": restored,
                "broken_no_cache": broken_no_cache,
                "empty_tips": empty_tips,
                "empty_sol": empty_sol,
                "bad_figs": bad,
                "fig_n": len(urls),
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
