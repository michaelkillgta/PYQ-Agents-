#!/usr/bin/env python3
import json
from pathlib import Path
from solve_ch19_common import solve_batch

REPAIRS = json.loads(Path("out-math/agents/chapter_19/repairs.json").read_text(encoding="utf-8"))
if __name__ == "__main__":
    solve_batch([31, 32, 42, 48, 59, 66, 73, 79], "b2", REPAIRS)
