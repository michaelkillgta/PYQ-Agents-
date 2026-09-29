import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

import pyq_common as p
p.configure_book("math")

from run_chapter_agents import v2_json
from agents.models import SOLVER_A
from test_repaired_ch9_23 import REPAIRS_CH9

env = p.load_env()
limiter = p.RateLimiter(60)

key_book = p.load_answer_key()
ch9_key = key_book.get("9", {}).get("answers", {})

SOLVER_SYSTEM = """Solve this JEE Main question.
Reply JSON {"answer":"..."} only.
MCQ answer is 1, 2, 3, or 4. Numerical answer is the number with no units.
Do not explain."""

def solve_one(item):
    q_no, data = item
    fmt = data["format"]
    body = data["body"]
    opts = data.get("options")
    k_val = ch9_key.get(str(q_no), {}).get("value")
    
    opt_lines = ""
    if opts:
        opt_lines = "\n".join(f"({i}) {o}" for i, o in enumerate(opts, start=1))
        
    user_prompt = f"Type: {fmt}\nStem:\n{body}\n{opt_lines}\n"
    messages = [
        {"role": "system", "content": SOLVER_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
    
    try:
        resp = v2_json(SOLVER_A, messages, env, limiter)
        model_ans = str(resp.get("answer", "")).strip()
    except Exception as exc:
        model_ans = f"ERROR: {exc}"
        
    return q_no, {
        "format": fmt,
        "key": str(k_val),
        "model": model_ans,
        "match": model_ans == str(k_val),
    }

results = {}
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(solve_one, item) for item in REPAIRS_CH9.items()]
    for fut in as_completed(futures):
        q_no, res = fut.result()
        results[q_no] = res
        print(f"Q{q_no:3d} [{res['format']:9s}] -> Key: {res['key']:5s} | GLM: {res['model']:5s} | Match: {res['match']}", flush=True)

with open("out-math/agents/chapter_9/sarvam_verification_23.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nVerification complete and saved to out-math/agents/chapter_9/sarvam_verification_23.json")
