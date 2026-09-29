#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding="utf-8")
import pyq_common as p
p.configure_book("math")
sb = p.supabase_client()
cid = p.resolve_chapter_id(sb, 33, "Mathematics")
rows = sb.table("pyq_questions").select("q_no,review_status,format").eq("chapter_id", cid).execute().data
from collections import Counter
st = Counter(r["review_status"] for r in rows)
fm = Counter(r["format"] for r in rows)
live = sum(1 for r in rows if r["review_status"] in ("auto_ok", "human_ok"))
held = sum(1 for r in rows if r["review_status"] not in ("auto_ok", "human_ok"))
print("cid", cid, "total", len(rows), "live", live, "held", held)
print("status", dict(st))
print("format", dict(fm))
