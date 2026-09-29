import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pyq_common import supabase_client, resolve_chapter_id, configure_book, load_skeleton, load_answer_key

configure_book('math')
skel = load_skeleton()
key = load_answer_key()

ch9_skel = [s for s in skel if s.get('chapter_no') == 9]
ch9_key = key.get('9', {})
pages = sorted(set(s['page'] for s in ch9_skel))

print('=== Chapter 9 Skeleton & Key ===')
print(f'Total questions in skeleton: {len(ch9_skel)}')
if pages:
    print(f'Page range: {min(pages)} to {max(pages)} ({len(pages)} pages: {pages})')
print(f"Answer key count: {len(ch9_key.get('answers', {}))}")

sb = supabase_client()
cid = resolve_chapter_id(sb, 9, 'Mathematics')
print(f'DB Chapter 9 ID: {cid}')

rows = sb.table('pyq_questions').select('id,q_no,review_status,format,correct_option,numerical_answer').eq('chapter_id', cid).order('q_no').execute().data
print(f'Total questions in DB: {len(rows)}')

status_dist = {}
for r in rows:
    st = r.get('review_status')
    status_dist[st] = status_dist.get(st, 0) + 1
print(f'Status distribution: {status_dist}')
