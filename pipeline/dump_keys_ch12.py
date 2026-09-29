import json
with open('out-math/skeleton.json', 'r', encoding='utf-8') as f:
    sk = json.load(f)
ch12_sk = {q['q_no']: q for q in sk if q.get('chapter_no') == 12}
for qno in sorted([17, 20, 21, 23, 25, 26, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 41, 42, 43, 44, 45, 46, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 59, 74, 78, 80, 83, 85, 86]):
    q = ch12_sk.get(qno, {})
    print(f"Q{qno:2d}: type={q.get('answer_type'):9s} ans={q.get('answer_value')}")
