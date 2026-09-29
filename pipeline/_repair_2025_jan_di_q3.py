"""Repair January 2025 DI Q3 piecewise so it matches the printed brace."""
from __future__ import annotations

import pyq_common as p

ROW_ID = "d916d79d-e39c-498f-96bb-de6eb38ecd5a"

MD = r"""<!-- paper-ocr -->

## Step 1: Integral Definition

Let
$I = 24 \int_{0}^{\frac{\pi}{2}} \left( \sin |4x - \frac{\pi}{12}| + [2 \sin x] \right) dx \dots(i)$
Now

## Step 2: Absolute Value Analysis

$|4x - \frac{\pi}{12}| = \begin{cases} -4x + \frac{\pi}{12} & ; x < \frac{\pi}{48} \\ 4x - \frac{\pi}{12} & ; x \ge \frac{\pi}{48} \end{cases}$
from (i)

## Step 3: Integral Decomposition

$I = 24 \int_{0}^{\frac{\pi}{48}} -\sin(4x - \frac{\pi}{12}) dx + \int_{\frac{\pi}{48}}^{\frac{\pi}{4}} \sin(4x - \frac{\pi}{12})$
$+ \int_{0}^{\frac{\pi}{6}} [2 \sin x] dx + \int_{\frac{\pi}{6}}^{\frac{\pi}{4}} [2 \sin x] dx$

## Step 4: Integration and Evaluation

$I = 24 \left( \frac{(1 - \cos \frac{\pi}{12})}{4} - \frac{(-\cos \frac{\pi}{12} - 1)}{4} \right) + \frac{\pi}{4} - \frac{\pi}{6}$
$I = 24 \left( \frac{1}{2} \right) + \frac{\pi}{4} - \frac{\pi}{6}$

## Step 5: Final Result Calculation

$I = 2\pi + 12 = 2\pi + \alpha$(from above)
$\therefore \alpha = 12$
"""


def main() -> None:
    sb = p.supabase_client()
    sb.table("pyq_questions").update({"solution_md": MD}).eq("id", ROW_ID).execute()
    row = sb.table("pyq_questions").select("solution_md").eq("id", ROW_ID).execute().data[0]
    body = row["solution_md"]
    assert r"\frac{\pi}{12}" in body
    assert r"\begin{cases}" in body
    assert r"\\ 4x - \frac{\pi}{12}" in body or r"\\\\ 4x" in body
    print("updated Q3 cases + pi/12", flush=True)


if __name__ == "__main__":
    main()
