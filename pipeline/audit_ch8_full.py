import json
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

from pyq_common import supabase_client, resolve_chapter_id, load_skeleton, load_answer_key, configure_book
from agents.katex_check import katex_render_ok, is_solver_dump
from audit_paper_text import flags_for

configure_book("math")
sb = supabase_client()
cid = resolve_chapter_id(sb, 8, "Mathematics")
res = sb.table("pyq_questions").select(
    "id,q_no,review_status,format,correct_option,numerical_answer,source_page,body,pyq_question_options(option_index,body)"
).eq("chapter_id", cid).order("q_no").execute().data

skel = load_skeleton()
key_book = load_answer_key()
ch8_skel = {s["q_no"]: s for s in skel if s.get("chapter_no") == 8}
ch8_key = key_book.get("8", {}).get("answers", {})

print(f"Total rows in DB: {len(res)}")

status_counts = {}
for r in res:
    st = r["review_status"]
    status_counts[st] = status_counts.get(st, 0) + 1
print("Status counts:", status_counts)

# Let's check each question
issues = []
for r in res:
    q = r["q_no"]
    st = r["review_status"]
    fmt = r["format"]
    body = (r["body"] or "").strip()
    opts = sorted(r.get("pyq_question_options") or [], key=lambda x: x.get("option_index", 0))
    k = ch8_key.get(str(q), {})
    
    # 1. Body check
    if not body:
        issues.append((q, st, "empty_body"))
    elif body.startswith("(OCR missed"):
        issues.append((q, st, "ocr_missed_body"))
    elif is_solver_dump(body):
        issues.append((q, st, "solver_dump_body"))
    
    # Audit text flags on body
    b_flags = flags_for(body, is_option=False)
    if b_flags:
        issues.append((q, st, f"body_flags:{b_flags}"))
        
    # KaTeX on body
    if body and not katex_render_ok(body):
        issues.append((q, st, "body_katex_fail"))
        
    # 2. Format & Options check
    if fmt == "numerical":
        num_ans = r.get("numerical_answer")
        if not num_ans or not str(num_ans).strip():
            issues.append((q, st, "missing_numerical_answer"))
    elif fmt == "mcq":
        corr_opt = r.get("correct_option")
        if corr_opt is None or corr_opt not in (1, 2, 3, 4):
            issues.append((q, st, f"bad_correct_option:{corr_opt}"))
        if len(opts) != 4:
            issues.append((q, st, f"opt_count_{len(opts)}"))
        for o in opts:
            obody = (o.get("body") or "").strip()
            if not obody:
                issues.append((q, st, f"opt_{o.get('option_index')}_empty"))
            else:
                o_flags = flags_for(obody, is_option=True)
                if o_flags:
                    issues.append((q, st, f"opt_{o.get('option_index')}_flags:{o_flags}"))
                if not katex_render_ok(obody):
                    issues.append((q, st, f"opt_{o.get('option_index')}_katex_fail"))
    else:
        issues.append((q, st, f"unexpected_format:{fmt}"))

print(f"\nTotal issue reports: {len(issues)}")
for q, st, iss in issues:
    print(f"  Q{q:3d} [{st:10s}] -> {iss}")
