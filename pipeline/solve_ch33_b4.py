#!/usr/bin/env python3
import json
from pathlib import Path
from solve_ch33_common import solve_batch

REPAIRS = json.loads(Path("out-math/agents/chapter_33/repairs.json").read_text(encoding="utf-8"))
if __name__ == "__main__":
    solve_batch([139, 144, 145, 154, 159, 160, 166], "b4", REPAIRS)
