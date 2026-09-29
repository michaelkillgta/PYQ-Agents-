#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
r = json.loads(Path("out-math/agents/chapter_33/repairs.json").read_text(encoding="utf-8"))
mm = [16, 23, 26, 29, 37, 42, 44, 51, 60, 61, 64, 72, 82, 84, 98, 112, 139, 144, 154, 166, 206, 246, 247, 252, 253, 262, 270, 276, 298]
for q in mm:
    d = r[str(q)]
    print("=" * 60)
    print(f"Q{q} {d['format']} key={d.get('correct_option') or d.get('numerical_answer')}")
    print(d["body"])
    if d.get("options"):
        for i, o in enumerate(d["options"], 1):
            print(f"  ({i}) {o}")
