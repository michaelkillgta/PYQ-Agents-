#!/usr/bin/env python3
import json
from pathlib import Path
from solve_ch19_common import solve_batch

REPAIRS = json.loads(Path("out-math/agents/chapter_19/repairs.json").read_text(encoding="utf-8"))
if __name__ == "__main__":
    solve_batch([134, 140, 144, 145, 146, 147, 148, 149], "b4", REPAIRS)
