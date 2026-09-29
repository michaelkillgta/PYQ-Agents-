import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import pyq_common as p
p.configure_book("math")

sb = p.supabase_client()
cid = p.resolve_chapter_id(sb, 12, "Mathematics")
print(f"Chapter 12 ID in DB: {cid}")

# Fetch questions from DB
rows = sb.table("pyq_questions").select(
    "id,q_no,review_status,format,correct_option,numerical_answer,body"
).eq("chapter_id", cid).order("q_no").execute().data

print(f"Total questions in DB for Chapter 12: {len(rows)}")

statuses = {}
formats = {}
for r in rows:
    statuses[r["review_status"]] = statuses.get(r["review_status"], 0) + 1
    formats[r["format"]] = formats.get(r["format"], 0) + 1

print(f"Review statuses: {statuses}")
print(f"Formats: {formats}")

held = [r for r in rows if r["review_status"] == "unreviewed"]
print(f"Held (unreviewed) questions count: {len(held)}")
if held:
    print(f"Held q_nos: {[r['q_no'] for r in held]}")

# Also check out-math/agents/chapter_12 files if any exist
import os
ch12_dir = "out-math/agents/chapter_12"
print(f"Does {ch12_dir} exist? {os.path.exists(ch12_dir)}")
if os.path.exists(ch12_dir):
    files = os.listdir(ch12_dir)
    print(f"Files in {ch12_dir}: {files}")
