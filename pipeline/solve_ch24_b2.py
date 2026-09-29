#!/usr/bin/env python3
import json
from pathlib import Path
from solve_ch24_common import solve_batch

REPAIRS = json.loads(Path("out-math/agents/chapter_24/repairs.json").read_text(encoding="utf-8"))
if __name__ == "__main__":
    solve_batch([29, 33, 44, 45, 46, 47, 48, 49], "b2", REPAIRS)
