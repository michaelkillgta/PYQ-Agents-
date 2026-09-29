import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import re
import fitz
import pyq_common as p
p.configure_book("math")

sb = p.supabase_client()
cid = p.resolve_chapter_id(sb, 12, "Mathematics")

# Fetch all 87 questions for ch 12 from DB
db_rows = sb.table("pyq_questions").select(
    "id,q_no,review_status,format,correct_option,numerical_answer,body"
).eq("chapter_id", cid).order("q_no").execute().data

db_by_no = {r["q_no"]: r for r in db_rows}
held_rows = [r for r in db_rows if r["review_status"] == "unreviewed"]
held_ids = [r["id"] for r in held_rows]

opts_res = sb.table("pyq_question_options").select("*").in_("question_id", held_ids).execute().data
opts_by_qid = {}
for o in opts_res:
    opts_by_qid.setdefault(o["question_id"], []).append(o)

with open("out-math/skeleton.json", "r", encoding="utf-8") as f:
    sk = json.load(f)
sk_by_no = {q["q_no"]: q for q in sk if q.get("chapter_no") == 12}

doc = fitz.open(r"c:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")

print(f"=== DETAILED REPORT ON ALL {len(held_rows)} HELD QUESTIONS ===")

for r in held_rows:
    q_no = r["q_no"]
    sk_q = sk_by_no.get(q_no, {})
    db_opts = sorted(opts_by_qid.get(r["id"], []), key=lambda x: x["option_index"])
    opt_texts = [o["body"] for o in db_opts]
    
    page_no = sk_q.get("page", 0)
    page = doc[page_no - 1]
    clip = fitz.Rect(sk_q.get("bbox", [0,0,600,800]))
    raw_pdf_text = page.get_text("text", clip=clip).strip()
    
    print(f"\n-------------------------------------------------------------")
    print(f"Q{q_no:2d} (p.{page_no}) | DB fmt: {r['format']} | Sk type: {sk_q.get('answer_type')} | Ans: {sk_q.get('answer_value')}")
    print(f"DB Body:\n{r['body']}")
    print(f"DB Options ({len(opt_texts)}): {opt_texts}")
    print(f"PDF Raw Clip:\n{raw_pdf_text}")

doc.close()
