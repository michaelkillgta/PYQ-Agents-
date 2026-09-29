#!/usr/bin/env python3
import json
from pathlib import Path
from solve_ch33_common import solve_batch

REPAIRS = json.loads(Path("out-math/agents/chapter_33/repairs.json").read_text(encoding="utf-8"))
if __name__ == "__main__":
    solve_batch([42, 44, 51, 60, 61, 64, 72], "b2", REPAIRS)
