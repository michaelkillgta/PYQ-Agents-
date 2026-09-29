#!/usr/bin/env python3
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import pyq_common as p

OUT = Path(r"c:\Users\tempo\Downloads\files\out-math-te-solutions\2024-apr\figures")
QID = "9b8144aa-5516-4114-991a-ac8663910097"
MD = r"""<!-- paper-ocr -->

## Step 1: Equation Setup

$\sin^2 x-(x^2-2x-2)\sin x-3(x-1)^2=0$

$\sin^2 x-(x-1)^2\sin x-3(x-1)^2=0$

## Step 2: Roots

roots: $\sin x=-3$ (reject) or $(x-1)^2$

[[fig:s2024apr_te_q03_2]]

## Step 3: Graph

$\sin x=(x-1)^2$

[[fig:s2024apr_te_q03_3]]
"""


def draw_v_tree(dest: Path) -> None:
    img = Image.new("RGB", (1100, 520), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 36)
        font_sm = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
        font_sm = font
    d.line([(220, 280), (550, 70), (880, 280)], fill=(20, 20, 20), width=10)
    d.text((40, 250), "roots :", fill=(20, 20, 20), font=font)
    d.text((250, 320), "-3", fill=(20, 20, 20), font=font)
    d.text((760, 320), "(x-1)\u00b2", fill=(20, 20, 20), font=font_sm)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "PNG")


def main() -> int:
    vpath = OUT / "s2024apr_te_q03_2.png"
    draw_v_tree(vpath)
    sb = p.supabase_client()
    for key in ("s2024apr_te_q03_2", "s2024apr_te_q03_3"):
        local = OUT / f"{key}.png"
        object_name = f"math/figures/{key}.png"
        sb.storage.from_(p.BUCKET).upload(
            object_name,
            local.read_bytes(),
            {"content-type": "image/png", "upsert": "true"},
        )
        print("uploaded", key, local.stat().st_size, flush=True)
    sb.table("pyq_questions").update({"solution_md": MD.strip() + "\n"}).eq("id", QID).execute()
    print("packet ok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
