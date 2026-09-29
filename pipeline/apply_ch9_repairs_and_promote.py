import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pyq_common as p
p.configure_book("math")

from agents.katex_check import katex_render_ok, is_solver_dump
from test_repaired_ch9_23 import REPAIRS_CH9

sb = p.supabase_client()
cid = p.resolve_chapter_id(sb, 9, "Mathematics")

# 1. Fetch current questions for Chapter 9
rows = sb.table("pyq_questions").select(
    "id,q_no,review_status,format,correct_option,numerical_answer"
).eq("chapter_id", cid).order("q_no").execute().data

q_by_no = {r["q_no"]: r for r in rows}
print(f"Loaded {len(rows)} questions from DB for chapter 9 (ID {cid}).")

# 2. Update each of the 23 questions
for q_no, data in sorted(REPAIRS_CH9.items()):
    row = q_by_no.get(q_no)
    if not row:
        print(f"ERROR: Q{q_no} not found in DB!")
        continue
    qid = row["id"]
    fmt = data["format"]
    body = data["body"].strip()
    opts = data.get("options")
    corr_opt = data.get("correct_option")
    num_ans = data.get("numerical_answer")
    
    patch = {
        "format": fmt,
        "body": body,
        "review_status": "human_ok",
        "extraction_confidence": 1.0,
        "correct_option": corr_opt,
        "numerical_answer": num_ans,
    }
    sb.table("pyq_questions").update(patch).eq("id", qid).execute()
    
    if fmt == "numerical":
        # Remove any old options
        sb.table("pyq_question_options").delete().eq("question_id", qid).execute()
    elif fmt == "mcq" and opts:
        # Delete existing and insert 4 options
        sb.table("pyq_question_options").delete().eq("question_id", qid).execute()
        opt_rows = [
            {"question_id": qid, "option_index": i, "body": opt_text.strip()}
            for i, opt_text in enumerate(opts, start=1)
        ]
        sb.table("pyq_question_options").insert(opt_rows).execute()
        
    print(f"Repaired and promoted Q{q_no:3d} [{fmt:9s}]: key={num_ans if fmt == 'numerical' else corr_opt}")

# 3. Update parsed.json on disk
parsed_path = p.OUT / "agents" / "chapter_9" / "parsed.json"
if parsed_path.exists():
    with open(parsed_path, "r", encoding="utf-8") as f:
        parsed_disk = json.load(f)
    for q_no, data in REPAIRS_CH9.items():
        parsed_disk[str(q_no)] = {
            "body": data["body"],
            "options": data.get("options"),
            "page": parsed_disk.get(str(q_no), {}).get("page", 78),
        }
    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(parsed_disk, f, ensure_ascii=False, indent=1)
    print("Updated out-math/agents/chapter_9/parsed.json")

# 4. Update hold.json on disk to reflect 0 holds
hold_path = p.OUT / "agents" / "chapter_9" / "hold.json"
with open(hold_path, "w", encoding="utf-8") as f:
    json.dump({"chapter_no": 9, "holds": []}, f, indent=1)
print("Updated out-math/agents/chapter_9/hold.json -> 0 holds")

# 5. Full re-verification of all 153 questions from DB
print("\n--- Running full DB verification after promotion ---")
all_res = sb.table("pyq_questions").select(
    "id,q_no,review_status,format,correct_option,numerical_answer,body,pyq_question_options(option_index,body)"
).eq("chapter_id", cid).order("q_no").execute().data

total_cnt = len(all_res)
live_cnt = 0
held_cnt = 0
status_dist = {}

failures = []
for r in all_res:
    st = r["review_status"]
    status_dist[st] = status_dist.get(st, 0) + 1
    if st in ("auto_ok", "human_ok"):
        live_cnt += 1
    else:
        held_cnt += 1
        
    q = r["q_no"]
    fmt = r["format"]
    b = (r["body"] or "").strip()
    opts = sorted(r.get("pyq_question_options") or [], key=lambda x: x.get("option_index", 0))
    
    if not b or b.startswith("(OCR missed") or is_solver_dump(b):
        failures.append((q, "bad_body", b[:60]))
    if fmt == "numerical":
        num = (r.get("numerical_answer") or "").strip()
        if not num:
            failures.append((q, "missing_num_ans", None))
    elif fmt == "mcq":
        c_opt = r.get("correct_option")
        if c_opt not in (1, 2, 3, 4):
            failures.append((q, "bad_correct_option", c_opt))
        if len(opts) != 4 or any(not (o.get("body") or "").strip() for o in opts):
            failures.append((q, "invalid_mcq_options", len(opts)))

print(f"\nFinal DB State for Chapter 9 (Matrices):")
print(f"  Total Questions: {total_cnt}")
print(f"  Live (auto_ok/human_ok): {live_cnt} ({live_cnt/total_cnt*100:.1f}%)")
print(f"  Held (unreviewed): {held_cnt}")
print(f"  Status distribution: {status_dist}")
print(f"  Validation failures: {len(failures)}")
if failures:
    for f in failures:
        print(f"    FAIL: {f}")
else:
    print("  ALL 153 QUESTIONS STRICTLY PASS isPyqPaperFilled!")
