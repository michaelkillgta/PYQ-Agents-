#!/usr/bin/env python3
import json
from pathlib import Path
from solve_ch24_common import solve_batch

REPAIRS = json.loads(Path("out-math/agents/chapter_24/repairs.json").read_text(encoding="utf-8"))
if __name__ == "__main__":
    solve_batch([50, 51, 52, 53, 54, 55, 56, 57], "b3", REPAIRS)
