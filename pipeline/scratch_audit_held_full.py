import json
import re
from pyq_common import supabase_client, resolve_chapter_id, configure_book, load_skeleton, load_answer_key
from parse_ocr_page import parse_digitise_to_questions
from repair_held_pyq import paper_spec
from agents.katex_check import katex_render_ok, is_solver_dump
from audit_paper_text import flags_for
from format_ocr_math import format_ocr_math

configure_book("math")
skel = load_skeleton()
key_book = load_answer_key()
ch6_specs = {s["q_no"]: s for s in skel if s.get("chapter_no") == 6}
ch6_key = key_book.get("6", {}).get("answers", {})

sb = supabase_client()
cid = resolve_chapter_id(sb, 6, "Mathematics")
rows = sb.table("pyq_questions").select(
    "id,q_no,review_status,format,body,correct_option,numerical_answer,source_page,pyq_question_options(option_index,body)"
).eq("chapter_id", cid).order("q_no").execute().data

held_rows = [r for r in rows if r["review_status"] not in ("auto_ok", "human_ok")]
held_q_nos = [r["q_no"] for r in held_rows]

# Load fresh OCR parses
all_ocr = {}
pages = sorted(set(s["page"] for s in ch6_specs.values()))
for p in pages:
    slice_ = [s for s in ch6_specs.values() if s["page"] == p]
    with open(f"out-math/ocr/page_{p:03d}.json", "r", encoding="utf-8") as f:
        payload = json.load(f)
    for q in parse_digitise_to_questions(payload, slice_):
        all_ocr[q["q_no"]] = q

# Recovered special cases
all_ocr[64] = {
    "q_no": 64,
    "body": "If the coefficient of $x^{30}$ in the expansion of $\\left(1 + \\frac{1}{x}\\right)^6 (1 + x^2)^7 (1 - x^3)^8$; $x \\neq 0$ is $\\alpha$, then $|\\alpha|$ equals __________.",
    "options": None,
}

all_ocr[10] = {
    "q_no": 10,
    "body": "If the ratio of the fifth term from the beginning to the fifth term from the end in the expansion of $\\left(\\sqrt[4]{2} + \\frac{1}{\\sqrt[4]{3}}\\right)^n$ is $\\sqrt{6} : 1$, then the third term from the beginning is:",
    "options": [
        "30\\sqrt{2}",
        "30\\sqrt{3}",
        "60\\sqrt{2}",
        "60\\sqrt{3}"
    ]
}

all_ocr[40] = {
    "q_no": 40,
    "body": "The missing value in the following figure is:\n\n[[fig:p049_x399]]",
    "options": None,
}

# Audit each held question
issues = []
ready = []

for r in held_rows:
    q = r["q_no"]
    spec = ch6_specs[q]
    k_ans = ch6_key.get(str(q), {})
    entry = all_ocr.get(q, {})
    
    body = (entry.get("body") or r.get("body") or "").strip()
    opts = entry.get("options")
    
    pspec = paper_spec(spec, {"body": body, "options": opts})
    fmt = "mcq" if pspec["answer_type"] == "mcq" else "numerical"
    
    # Specific override if known numerical
    if q in (19, 21, 25, 28, 37, 40, 64, 68, 73, 75, 80, 84, 107, 112, 115, 117, 120, 122, 123, 124, 140, 141, 142, 143, 145, 149, 150, 151, 152, 153, 154, 156, 184, 189, 191, 192, 193, 194, 195, 196, 200):
        fmt = "numerical"
        opts = None
    
    if fmt == "mcq":
        if not opts or len(opts) != 4 or any(not (o or "").strip() for o in opts):
            issues.append((q, "missing_options", opts))
            continue
    else:
        ans_val = k_ans.get("value")
        if not ans_val:
            issues.append((q, "missing_answer_key", k_ans))
            continue
            
    # KaTeX checks
    fields = [body]
    if opts:
        fields.extend(opts)
    bad_katex = [t for t in fields if not katex_render_ok(t)]
    if bad_katex:
        issues.append((q, "katex_error", bad_katex[0][:60]))
        continue
        
    ready.append({
        "q_no": q,
        "format": fmt,
        "body": body,
        "options": opts,
        "answer": k_ans.get("value")
    })

print(f"Total ready without issues: {len(ready)} / {len(held_rows)}")
print(f"Total with issues: {len(issues)}")
for iss in issues:
    print("Issue:", iss)
