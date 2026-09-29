#!/usr/bin/env python3
import json
from pathlib import Path
from solve_ch24_common import solve_batch

REPAIRS = json.loads(Path("out-math/agents/chapter_24/repairs.json").read_text(encoding="utf-8"))
if __name__ == "__main__":
    solve_batch([66, 67, 68, 69, 70, 71, 72, 73], "b5", REPAIRS)
