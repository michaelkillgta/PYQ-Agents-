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

# Load skeleton
with open("out-math/skeleton.json", "r", encoding="utf-8") as f:
    sk = json.load(f)
sk_by_no = {q["q_no"]: q for q in sk if q.get("chapter_no") == 12}

print(f"Loaded {len(db_rows)} DB questions, {len(held_rows)} held, {len(sk_by_no)} skeleton.")

# Open PDF
doc = fitz.open(r"c:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf")

# Let's inspect Q17, Q53, Q59 specifically to see their format and options
special_qnos = [17, 29, 33, 43, 53, 59]
for q_no in special_qnos:
    r = db_by_no[q_no]
    sk_q = sk_by_no[q_no]
    opts = opts_by_qid.get(r["id"], [])
    print(f"\n=================== SPECIAL CHECK Q{q_no} ===================")
    print(f"DB format: {r['format']}, review: {r['review_status']}, num_ans: {r['numerical_answer']}, corr_opt: {r['correct_option']}")
    print(f"Skeleton: type={sk_q.get('answer_type')}, ans={sk_q.get('answer_value')}, page={sk_q.get('page')}, bbox={sk_q.get('bbox')}")
    print(f"DB opts count: {len(opts)}")
    print(f"DB body snippet:\n{r['body'][:300]}")
    
    # Extract text from page bbox
    page = doc[sk_q['page'] - 1]
    bbox = fitz.Rect(sk_q['bbox'])
    pdf_text = page.get_text("text", clip=bbox)
    print(f"PDF clip text:\n{pdf_text}")

doc.close()
