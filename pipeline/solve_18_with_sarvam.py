import json
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

import pyq_common as p
p.configure_book("math")
from run_chapter_agents import v2_json
from agents.models import SOLVER_A
from test_repaired_18 import REPAIRS

env = p.load_env()
limiter = p.RateLimiter(60)

key_book = p.load_answer_key()
ch8_key = key_book.get("8", {}).get("answers", {})

SOLVER_SYSTEM = """Solve this JEE Main question.
Reply JSON {"answer":"..."} only.
MCQ answer is 1, 2, 3, or 4. Numerical answer is the number with no units.
Do not explain."""

results = {}

for q_no, data in sorted(REPAIRS.items()):
    fmt = data["format"]
    body = data["body"]
    opts = data.get("options")
    k_val = ch8_key.get(str(q_no), {}).get("value")
    
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
        
    results[q_no] = {
        "format": fmt,
        "key": str(k_val),
        "model": model_ans,
        "match": model_ans == str(k_val),
    }
    print(f"Q{q_no:3d} [{fmt:9s}] -> Key: {str(k_val):5s} | GLM: {model_ans:5s} | Match: {model_ans == str(k_val)}")

with open("out-math/agents/chapter_8/sarvam_verification_18.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nVerification complete and saved to out-math/agents/chapter_8/sarvam_verification_18.json")
