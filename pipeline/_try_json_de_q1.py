"""See why the two DE Q1 blobs fail json.loads."""
from __future__ import annotations

import json
from pathlib import Path

import pyq_common as p

ROOT = Path(r"c:\Users\tempo\Downloads\files\out-math-2025-paper-solutions")


def try_load(label: str, text: str) -> None:
    print("====", label, "len", len(text))
    try:
        json.loads(text)
        print(" raw json ok")
    except Exception as exc:
        print(" raw json", type(exc).__name__, exc)
    blob = p.salvage_tex_json(text)
    try:
        json.loads(blob)
        print(" salvage ok")
    except Exception as exc:
        print(" salvage", type(exc).__name__, exc)
        start, end = blob.find("{"), blob.rfind("}")
        print(" braces", start, end, "tail", repr(blob[-80:]))


def main() -> None:
    for name in ("raw_2025-apr_de_q01.txt", "raw_2025-jan_de_q01.txt"):
        text = (ROOT / name).read_text(encoding="utf-8")
        try_load(name, text)


if __name__ == "__main__":
    main()
