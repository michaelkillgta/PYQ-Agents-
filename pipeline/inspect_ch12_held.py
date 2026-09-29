import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import pyq_common as p
p.configure_book("math")

sb = p.supabase_client()
cid = p.resolve_chapter_id(sb, 12, "Mathematics")

# Load skeleton for ch 12
with open("out-math/skeleton.json", "r", encoding="utf-8") as f:
    sk = json.load(f)
sk_ch12 = {q["q_no"]: q for q in sk if q.get("chapter_no") == 12}

# Load parsed.json for ch 12 if exists
parsed_ch12 = {}
try:
    with open("out-math/agents/chapter_12/parsed.json", "r", encoding="utf-8") as f:
        parsed_data = json.load(f)
        if isinstance(parsed_data, list):
            parsed_ch12 = {q["q_no"]: q for q in parsed_data if "q_no" in q}
        elif isinstance(parsed_data, dict):
            # check if dict of q_no or wrapped
            if "questions" in parsed_data:
                parsed_ch12 = {q["q_no"]: q for q in parsed_data["questions"]}
            else:
                for k, v in parsed_data.items():
                    if isinstance(v, dict) and "q_no" in v:
                        parsed_ch12[v["q_no"]] = v
                    elif isinstance(v, dict):
                        try:
                            parsed_ch12[int(k)] = v
                        except:
                            pass
except Exception as e:
    print(f"Error loading parsed.json: {e}")

# Fetch questions from DB
db_rows = sb.table("pyq_questions").select(
    "id,q_no,review_status,format,correct_option,numerical_answer,body"
).eq("chapter_id", cid).order("q_no").execute().data

# Also fetch options for held questions
held_ids = [r["id"] for r in db_rows if r["review_status"] == "unreviewed"]
opts_res = sb.table("pyq_question_options").select("*").in_("question_id", held_ids).execute().data
opts_by_qid = {}
for opt in opts_res:
    opts_by_qid.setdefault(opt["question_id"], []).append(opt)

db_by_no = {r["q_no"]: r for r in db_rows}
held_rows = [r for r in db_rows if r["review_status"] == "unreviewed"]

print(f"Total held rows: {len(held_rows)}")

from agents.katex_check import (
    dollar_runs_ok,
    leftover_latex_outside_math,
    probe_tex,
    _MATH_INNER,
    is_solver_dump,
)

def check_katex_detail(text):
    if not dollar_runs_ok(text):
        return False, "unbalanced_dollars"
    if leftover_latex_outside_math(text):
        return False, "leftover_latex_outside_math"
    for m in _MATH_INNER.finditer(text or ""):
        if not probe_tex(m.group(1)):
            return False, f"probe_failed: {m.group(1)[:40]}"
    return True, "ok"

held_analysis = []
for r in held_rows:
    q_no = r["q_no"]
    qid = r["id"]
    fmt = r["format"]
    body = r["body"] or ""
    db_opts = sorted(opts_by_qid.get(qid, []), key=lambda x: x["option_index"])
    opt_texts = [o["body"] for o in db_opts]
    
    sk_q = sk_ch12.get(q_no, {})
    sk_ans = sk_q.get("answer_value")
    sk_type = sk_q.get("answer_type")
    page = sk_q.get("page")
    
    body_ok, body_err = check_katex_detail(body)
    dump = is_solver_dump(body)
    opts_ok = True
    opt_errs = []
    for i, ot in enumerate(opt_texts):
        ook, oerr = check_katex_detail(ot)
        if not ook:
            opts_ok = False
            opt_errs.append((i, oerr))
            
    held_analysis.append({
        "q_no": q_no,
        "page": page,
        "db_format": fmt,
        "sk_type": sk_type,
        "sk_ans": sk_ans,
        "body_ok": body_ok,
        "body_err": body_err,
        "is_dump": dump,
        "opts_count": len(db_opts),
        "opts_ok": opts_ok,
        "opt_errs": opt_errs,
        "body_snippet": body[:120].replace("\n", " "),
        "opts": opt_texts,
    })

with open("out-math/agents/chapter_12/held_analysis_39.json", "w", encoding="utf-8") as f:
    json.dump(held_analysis, f, indent=2, ensure_ascii=False)

print(f"Saved analysis of {len(held_analysis)} held questions to held_analysis_39.json")
for ha in held_analysis:
    flags = []
    if not ha['body_ok']:
        flags.append(f"body_err: {ha['body_err']}")
    if ha['is_dump']:
        flags.append("SOLVER_DUMP")
    if ha['opts_count'] != (4 if ha['db_format'] == 'mcq' else 0):
        flags.append(f"opts_count={ha['opts_count']}(expected {4 if ha['db_format']=='mcq' else 0})")
    if not ha['opts_ok']:
        flags.append(f"opt_errs: {ha['opt_errs']}")
    print(f"Q{ha['q_no']:2d} (p.{ha['page']}) [{ha['db_format']}/{ha['sk_type']}] ans={ha['sk_ans']} | " + "; ".join(flags if flags else ["clean text"]))
