#!/usr/bin/env python3
"""Corner audit of the ten screenshot Maths chapters. No publish."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

import pyq_common as p
from agents.katex_check import katex_render_ok, smashed_tex
from audit_paper_text import flags_for

SUBJECT = "Mathematics"
FILES = Path(r"c:\Users\tempo\Downloads\files")
SLUGS = {
    1: ("basic-of-mathematics", "bom"),
    3: ("complex-number", "cn"),
    6: ("binomial-theorem", "bt"),
    9: ("determinants", "det"),
    14: ("continuity-and-differentiability", "cad"),
    15: ("application-of-derivatives", "aod"),
    17: ("definite-integration", "di"),
    18: ("area-under-curves", "auc"),
    19: ("differential-equations", "de"),
    21: ("circle", "cir"),
}
FIG_RE = re.compile(r"\[\[fig:([a-zA-Z0-9_]+)\]\]")
RASTER_KEY = re.compile(r"^(?:p\d+_x\d+|s\d{4}[a-z]{0,3}(?:_[a-z]+)?_q\d+_\d+)$", re.I)
NESTED_FRAC = re.compile(r"\\frac\s*\{\s*\\frac")
ASCII_SQRT = re.compile(r"\bsqrt\d|\bSQRT|1/sqrt", re.I)
BEGIN_ALIGNED = re.compile(r"\\begin\{aligned\}")
PAPER = "<!-- paper-ocr -->"
STEP = re.compile(r"^##\s+Step\s+\d+", re.M)
SELECT = (
    "id,q_no,review_status,exam_date,source_bbox,format,body,solution_md,tips_md,formulas_md,"
    "correct_option,numerical_answer,"
    "question_options:pyq_question_options(option_index,body),"
    "figure_links:pyq_figure_links(role,sort_order,figures:pyq_figures(figure_key,storage_path,public_url))"
)


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def math_chapters(sb):
    sid = sb.table("pyq_subjects").select("id").eq("name", SUBJECT).execute().data[0]["id"]
    units = [u["id"] for u in sb.table("pyq_units").select("id").eq("subject_id", sid).execute().data]
    rows = (
        sb.table("pyq_chapters")
        .select("id,chapter_no,catalog_slug,name")
        .in_("unit_id", units)
        .in_("catalog_slug", [s[0] for s in SLUGS.values()])
        .execute()
        .data
        or []
    )
    return sorted(rows, key=lambda r: int(r["chapter_no"]))


def fetch_all(sb, chapter_id: str) -> list[dict]:
    out = []
    start = 0
    while True:
        chunk = (
            sb.table("pyq_questions")
            .select(SELECT)
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


def booklet_of(row: dict) -> str:
    return str((row.get("source_bbox") or {}).get("booklet") or "")


def printed_from_disk(short: str) -> dict[str, int]:
    root = FILES / f"out-math-{short}"
    found = {}
    if not root.is_dir():
        return found
    for inv in root.glob("*/inventory.json"):
        data = json.loads(inv.read_text(encoding="utf-8"))
        found[str(data.get("id") or inv.parent.name)] = int(data.get("printed_count") or 0)
    return found


def fig_keys(text: str) -> list[str]:
    return FIG_RE.findall(text or "")


def linked_keys(row: dict) -> list[str]:
    keys = []
    for link in row.get("figure_links") or []:
        fig = link.get("figures")
        if isinstance(fig, list):
            fig = fig[0] if fig else {}
        if isinstance(fig, dict) and fig.get("figure_key"):
            keys.append(fig["figure_key"])
    return keys


def public_url(fig: dict, env: dict) -> str:
    stored = (fig.get("public_url") or "").strip()
    if stored:
        return stored
    base = (env.get("NEXT_PUBLIC_SUPABASE_URL") or env.get("SUPABASE_URL") or "").rstrip("/")
    path = str(fig.get("storage_path") or "").lstrip("/")
    if not path.startswith("pyq/"):
        path = f"pyq/{path}"
    return f"{base}/storage/v1/object/public/{path}"


def check_row(row: dict, chapter: dict) -> dict:
    hits = []
    live = row.get("review_status") in {"auto_ok", "human_ok"}
    opts = sorted(row.get("question_options") or [], key=lambda o: int(o.get("option_index") or 0))
    bodies = [row.get("body") or ""] + [str(o.get("body") or "") for o in opts]
    sol = row.get("solution_md") or ""
    label = f"ch{chapter['chapter_no']} q{row['q_no']} {booklet_of(row)}"

    if live:
        for i, text in enumerate(bodies):
            where = "stem" if i == 0 else f"opt{i}"
            if flags_for(text, is_option=i > 0):
                hits.append(f"{where}-junk:{flags_for(text, is_option=i > 0)}")
            if smashed_tex(text):
                hits.append(f"{where}-smashed")
            if not katex_render_ok(text):
                hits.append(f"{where}-katex")
        if not sol.strip():
            hits.append("empty-solution")
        else:
            if smashed_tex(sol):
                hits.append("sol-smashed")
            if NESTED_FRAC.search(sol):
                hits.append("sol-nested-frac")
            if PAPER in sol and not STEP.search(sol):
                hits.append("paper-no-steps")
            if not katex_render_ok(sol):
                hits.append("sol-katex")
        tips = row.get("tips_md") or ""
        forms = row.get("formulas_md") or ""
        if sol.strip() and not tips.strip():
            hits.append("empty-tips")
        if ASCII_SQRT.search(forms) or ASCII_SQRT.search(tips):
            hits.append("ascii-sqrt")
        if BEGIN_ALIGNED.search(forms):
            hits.append("raw-aligned")
        for key in fig_keys((row.get("body") or "") + "\n" + sol):
            if not RASTER_KEY.match(key):
                hits.append(f"bad-fig-key:{key}")
        stem_figs = fig_keys(row.get("body") or "")
        linked = linked_keys(row)
        if stem_figs and not linked:
            hits.append("stem-fig-no-link")
    return {"label": label, "id": row["id"], "hits": hits, "live": live, "row": row}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    env = p.load_env()
    sb = p.supabase_client()
    chapters = math_chapters(sb)
    report = {"chapters": [], "hits": []}
    rows_for_katex = []
    all_fig_urls = []
    print("loading rows", flush=True)
    for ch in chapters:
        rows = fetch_all(sb, ch["id"])
        live = [r for r in rows if r.get("review_status") in {"auto_ok", "human_ok"}]
        held = [r for r in rows if r.get("review_status") not in {"auto_ok", "human_ok"}]
        by_book = defaultdict(int)
        for r in live:
            by_book[booklet_of(r) or "?"] += 1
        disk = printed_from_disk(SLUGS[int(ch["chapter_no"])][1])
        miss_books = []
        for bid, n in sorted(disk.items()):
            got = by_book.get(bid, 0)
            if n and got < n:
                miss_books.append({"booklet": bid, "printed": n, "live": got})
        rec = {
            "chapter_no": ch["chapter_no"],
            "slug": ch["catalog_slug"],
            "rows": len(rows),
            "live": len(live),
            "held": len(held),
            "by_booklet": dict(by_book),
            "disk_printed": disk,
            "live_short_of_printed": miss_books,
            "empty_sol": sum(1 for r in live if not (r.get("solution_md") or "").strip()),
            "empty_tips": sum(
                1
                for r in live
                if (r.get("solution_md") or "").strip() and not (r.get("tips_md") or "").strip()
            ),
        }
        report["chapters"].append(rec)
        print(
            f"  ch{ch['chapter_no']} live={len(live)} held={len(held)} "
            f"short={miss_books} empty_sol={rec['empty_sol']} empty_tips={rec['empty_tips']}",
            flush=True,
        )
        rows_for_katex.extend((ch, r) for r in rows)
        for r in live:
            for link in r.get("figure_links") or []:
                fig = link.get("figures")
                if isinstance(fig, list):
                    fig = fig[0] if fig else {}
                if isinstance(fig, dict) and fig.get("figure_key"):
                    all_fig_urls.append((fig["figure_key"], public_url(fig, env)))

    print(f"katex+pattern scan {len(rows_for_katex)} rows", flush=True)
    hits = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(check_row, r, ch) for ch, r in rows_for_katex]
        for fut in as_completed(futs):
            item = fut.result()
            if item["hits"]:
                hits.append({"label": item["label"], "id": item["id"], "hits": item["hits"]})
    hits.sort(key=lambda x: x["label"])
    report["hits"] = hits
    print(f"pattern hits {len(hits)}", flush=True)
    by_kind = defaultdict(int)
    for item in hits:
        for h in item["hits"]:
            by_kind[h.split(":")[0]] += 1
    for k, n in sorted(by_kind.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {n}", flush=True)

    uniq = dict(all_fig_urls)
    print(f"GET {len(uniq)} figure URLs", flush=True)
    bad_get = []
    def ping(pair):
        key, url = pair
        try:
            r = httpx.get(url, timeout=20.0)
            return key, url, r.status_code, len(r.content)
        except Exception as exc:
            return key, url, 0, str(exc)
    with ThreadPoolExecutor(max_workers=16) as pool:
        for key, url, status, nbytes in pool.map(ping, uniq.items()):
            if status != 200 or (isinstance(nbytes, int) and nbytes < 24):
                bad_get.append({"key": key, "status": status, "bytes": nbytes})
    report["bad_figure_gets"] = bad_get
    print(f"bad figure GET {len(bad_get)}", flush=True)

    dest = FILES / "out-math-named" / "corner_audit.json"
    dump(dest, report)
    print(f"wrote {dest}", flush=True)
    return 0 if not hits and not bad_get and not any(c["live_short_of_printed"] or c["empty_sol"] for c in report["chapters"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
