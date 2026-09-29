#!/usr/bin/env python3
import json
from pathlib import Path
from solve_ch19_common import solve_batch

REPAIRS = json.loads(Path("out-math/agents/chapter_19/repairs.json").read_text(encoding="utf-8"))
if __name__ == "__main__":
    solve_batch([150, 151, 152, 153, 154, 155, 165, 167], "b5", REPAIRS)
