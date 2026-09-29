import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pyq_common import supabase_client, resolve_chapter_id, load_skeleton, load_answer_key, configure_book

configure_book("math")
sb = supabase_client()
cid = resolve_chapter_id(sb, 8, "Mathematics")
res = sb.table("pyq_questions").select(
    "id,q_no,review_status,format,correct_option,numerical_answer,source_page,body,pyq_question_options(option_index,body)"
).eq("chapter_id", cid).order("q_no").execute().data

held = [r for r in res if r.get("review_status") not in ("auto_ok", "human_ok")]
print(f"Held count: {len(held)}")

skel = load_skeleton()
key_book = load_answer_key()
ch8_skel = {s["q_no"]: s for s in skel if s.get("chapter_no") == 8}
ch8_key = key_book.get("8", {}).get("answers", {})

for h in held:
    q = h["q_no"]
    opts = sorted(h.get("pyq_question_options") or [], key=lambda x: x.get("option_index", 0))
    k = ch8_key.get(str(q), {})
    print(f"\n--- Q{q} (Page {h.get('source_page')}) ---")
    print(f"Status: {h['review_status']}, Format: {h['format']}")
    print(f"DB Ans: opt={h['correct_option']}, num={h['numerical_answer']}")
    print(f"Key: {k}")
    print(f"Body: {repr(h['body'][:120]) if h['body'] else 'None'}")
    print(f"Opts count: {len(opts)}")
    for o in opts:
        print(f"  [{o.get('option_index')}]: {repr(o.get('body'))}")
