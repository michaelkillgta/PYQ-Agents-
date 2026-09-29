#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import generate_di_coach as di
import pyq_common as p

QID = "884ccf93-57dd-4d9f-835a-08903776a152"
SRC = Path(r"c:\Users\tempo\Downloads\files\out-math-pyq-coach\glm") / f"{QID}.json"


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    for rec in data["tips"]:
        rec["body"] = (
            rec["body"]
            .replace("option 1", "the first claim")
            .replace("option 4", "the min-max claim")
            .replace("option 3", "the equality claim")
        )
    parsed = di.validate(data)
    if not parsed:
        raise SystemExit("still invalid after leak strip")
    tips, formulas = parsed
    sb = p.supabase_client()
    sb.table("pyq_questions").update(
        {
            "tips_md": json.dumps({"tips": tips}, ensure_ascii=False),
            "formulas_md": json.dumps({"formulas": formulas}, ensure_ascii=False),
        }
    ).eq("id", QID).execute()
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("published aod q61 coach", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
