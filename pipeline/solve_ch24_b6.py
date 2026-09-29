#!/usr/bin/env python3
import json
from pathlib import Path
from solve_ch24_common import solve_batch

REPAIRS = json.loads(Path("out-math/agents/chapter_24/repairs.json").read_text(encoding="utf-8"))
if __name__ == "__main__":
    solve_batch([74, 75, 88, 89, 90, 91, 92, 93], "b6", REPAIRS)
