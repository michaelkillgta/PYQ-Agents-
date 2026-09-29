import os
from supabase import create_client

env_vars = {}
with open(r'c:\Users\tempo\Downloads\EduBlast\Web\.env.local', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env_vars[k.strip()] = v.strip().strip('"\'')

supabase = create_client(env_vars['NEXT_PUBLIC_SUPABASE_URL'], env_vars['SUPABASE_SERVICE_ROLE_KEY'])
res = supabase.table('pyq_chapters').select('*').eq('catalog_slug', 'sets-and-relations').execute()
print('pyq_chapters for sets-and-relations:', res.data)
if res.data:
    cid = res.data[0]['id']
    q_res = supabase.table('pyq_questions').select('id, question_number, review_status, format').eq('chapter_id', cid).order('question_number').execute()
    print('Total questions in DB:', len(q_res.data))
    statuses = {}
    for q in q_res.data:
        statuses[q['review_status']] = statuses.get(q['review_status'], 0) + 1
    print('Review statuses in DB:', statuses)
