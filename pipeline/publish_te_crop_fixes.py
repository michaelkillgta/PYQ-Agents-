#!/usr/bin/env python3
"""Crop-faithful TE solution_md. Crop PNG is source of truth."""
from __future__ import annotations

import pyq_common as p

PACKETS: dict[str, str] = {
    "8502255f-df5d-4a0c-b5ef-1f33fd119c06": """<!-- paper-ocr -->

## Step 1: Initial Equation Setup

$\\dfrac{\\tan(x+100^\\circ)}{\\tan x}=\\tan(x+50^\\circ)\\tan(x-50^\\circ)$

$\\dfrac{\\sin(x+100^\\circ)\\cos x}{\\cos(x+100^\\circ)\\sin x}=\\dfrac{\\sin(x+50^\\circ)\\sin(x-50^\\circ)}{\\cos(x+50^\\circ)\\cos(x-50^\\circ)}$

## Step 2: Componendo and Dividendo Application

Applying Componendo & Dividendo:

$\\dfrac{\\sin(2x+100^\\circ)}{\\sin 100^\\circ}=\\dfrac{\\cos 100^\\circ}{-\\cos 2x}$

## Step 3: Trigonometric Simplification

$2\\sin(2x+100^\\circ)\\cos 2x+\\sin 200^\\circ=0$

$\\sin(4x+100^\\circ)+\\sin 100^\\circ+\\sin 200^\\circ=0$

$\\sin(4x+100^\\circ)=-2\\sin 150^\\circ\\cos 50^\\circ$

$\\sin(4x+100^\\circ)=-\\cos 50^\\circ=\\sin(-40^\\circ)$

## Step 4: General Solution Derivation

$\\therefore 4x+100^\\circ=n\\pi+(-1)^n(-40^\\circ)$

$x=\\dfrac{n\\pi+(-1)^{n+1}(40^\\circ)-100^\\circ}{4}$

## Step 5: Final Solution Count

$\\therefore x=30^\\circ,55^\\circ,120^\\circ,145^\\circ$ in $(0,\\pi)$

$\\therefore$ Number of solutions $=4$
""",
    "bbcaebf5-d69f-4743-8b9a-2938086d0d26": """<!-- paper-ocr -->

## Step 1: Substitution and Equation Setup

$10(\\sin^2\\theta)^2+15(1-\\sin^2\\theta)^2=6$

Let $\\sin^2\\theta=t\\Rightarrow 10t^2+15(1-t)^2=16$

## Step 2: Quadratic Simplification

$10t^2+15-30t+15t^2=6$

$25t^2-30t+9=0$

$(5t-3)^2=0$

## Step 3: Solving for Trigonometric Values

$\\sin^2\\theta=\\dfrac{3}{5}$ and $\\cos^2\\theta=\\dfrac{2}{5}$

## Step 4: Final Numerical Evaluation

$\\dfrac{27\\times\\dfrac{125}{27}+8+\\dfrac{125}{8}}{16\\left(\\dfrac{5}{2}\\right)^4}=\\dfrac{250}{125\\times 5}=\\dfrac{2}{5}$
""",
    "41e37d38-b2fc-4ed5-87b3-a90989ad3d79": """<!-- paper-ocr -->

## Step 1: Solving first equation

$2\\sin^2\\theta=\\cos 2\\theta$

$2\\sin^2\\theta=1-2\\sin^2\\theta$

$4\\sin^2\\theta=1$

$\\sin^2\\theta=\\dfrac{1}{4}$

$\\sin\\theta=\\pm\\dfrac{1}{2}$

## Step 2: Solving second equation

$2\\cos^2\\theta=3\\sin\\theta$

$2-2\\sin^2\\theta+3\\sin\\theta-2=0$

$(2\\sin\\theta-1)(2\\sin\\theta-2)=0$

$\\sin\\theta=\\dfrac{1}{2}$

## Step 3: Finding common solution

so common equation which satisfy both equations is $\\sin\\theta=\\dfrac{1}{2}$

$\\theta=\\dfrac{\\pi}{6},\\dfrac{5\\pi}{6}\\quad(\\theta\\in[0,2\\pi])$

## Step 4: Final evaluation

Sum $=\\pi$
""",
    "5693daf3-27ac-483a-a37b-7fe002835142": """<!-- paper-ocr -->

## Step 1: Expression for tan theta

$x=3\\left(\\dfrac{\\tan\\theta+\\sqrt{3}}{1-\\sqrt{3}\\tan\\theta}\\right)$

$x-\\sqrt{3}\\tan\\theta=3\\tan\\theta+3\\sqrt{3}$

$\\tan\\theta=\\dfrac{x-3\\sqrt{3}}{3+\\sqrt{3}x}\\dots(1)$

## Step 2: Relation between y and tan theta

$2\\left(\\dfrac{\\tan\\theta+\\dfrac{1}{\\sqrt{3}}}{1-\\dfrac{\\tan\\theta}{\\sqrt{3}}}=y\\right)$

$2(\\sqrt{3}\\tan\\theta+1)=y(\\sqrt{3}-\\tan\\theta)\\dots(2)$

## Step 3: Substitution and simplification

using (1) and (2)

$2\\left(\\dfrac{x-3\\sqrt{3}}{\\sqrt{3}+x}+1\\right)=y\\left(\\sqrt{3}-\\dfrac{(x-3\\sqrt{3})}{\\sqrt{3}(\\sqrt{3}+x)}\\right)$

$2\\sqrt{3}(x-3\\sqrt{3}+x+\\sqrt{3})=y\\bigl(3(\\sqrt{3}+x)-x+3\\sqrt{3}\\bigr)$

$4\\sqrt{3}x-12=y(2x+6\\sqrt{3})$

## Step 4: Equation of hyperbola

$xy-2\\sqrt{3}x+3\\sqrt{3}y-6=0$

$\\Rightarrow\\alpha=-2\\sqrt{3},\\beta=3\\sqrt{3},\\gamma=-6$

## Step 5: Final evaluation

$\\alpha^2+\\beta^2+\\gamma^2=12+27+36=75$
""",
    "7ae4e847-50c7-4fd4-8881-1ff64ff82b67": """<!-- paper-ocr -->

## Step 1: Substitution and Simplification

$4\\left(\\dfrac{1-\\tan^2\\theta/2}{1+\\tan^2\\theta/2}\\right)-3\\left(\\dfrac{2\\tan\\dfrac{\\theta}{2}}{1+\\tan^2\\dfrac{\\theta}{2}}\\right)=1$

let $\\tan\\dfrac{\\theta}{2}=t$

$\\dfrac{4-4t^2-6t}{1+t^2}=1$

$4-4t^2-6t=1+t^2$

## Step 2: Solving Quadratic Equation

$\\Rightarrow 5t^2+6t-3=0$

$\\Rightarrow t=\\dfrac{-6\\pm\\sqrt{36-4(5)(-3)}}{2(5)}$

$=\\dfrac{-6\\pm\\sqrt{96}}{10}$

$=\\dfrac{-6\\pm 4\\sqrt{6}}{10}$

$t=\\dfrac{-3+2\\sqrt{6}}{5}$

## Step 3: Calculating Cosine Value

$\\cos\\theta=\\dfrac{1-t^2}{1+t^2}=\\dfrac{1-\\left(\\dfrac{2\\sqrt{6}-3}{5}\\right)^2}{1+\\left(\\dfrac{2\\sqrt{6}-3}{5}\\right)^2}=\\dfrac{1-\\left(\\dfrac{24+9-12\\sqrt{6}}{25}\\right)}{1+\\left(\\dfrac{24+9-12\\sqrt{6}}{25}\\right)}$

$=\\dfrac{25-33+12\\sqrt{6}}{25}=\\dfrac{12\\sqrt{6}-8}{25}=\\dfrac{6\\sqrt{6}-4}{25}=\\dfrac{4-6\\sqrt{6}}{25}\\times\\dfrac{29+6\\sqrt{6}}{29+6\\sqrt{6}}$

$=\\dfrac{25+33-12\\sqrt{6}}{100+150\\sqrt{6}}=\\dfrac{58-12\\sqrt{6}}{25}=\\dfrac{29-6\\sqrt{6}}{25}$

$=25(4-6\\sqrt{6})\\dfrac{1}{4-6\\sqrt{6}}=3\\sqrt{6}-2$
""",
    "9b8144aa-5516-4114-991a-ac8663910097": """<!-- paper-ocr -->

## Step 1: Equation Setup

$\\sin^2 x-(x^2-2x-2)\\sin x-3(x-1)^2=0$

$\\sin^2 x-(x-1)^2\\sin x-3(x-1)^2=0$

## Step 2: Roots

roots: $\\sin x=-3$ (reject) or $(x-1)^2$

## Step 3: Graph

$\\sin x=(x-1)^2$

[[fig:s2024apr_te_q03_1]]
""",
    "c6565c55-ef48-42f6-8fed-75af62a2aa9e": """<!-- paper-ocr -->

## Step 1: Trigonometric Substitution

$2\\tan^2\\theta-5\\sec\\theta-1=0$

$\\Rightarrow 2\\sec^2\\theta-5\\sec\\theta-3=0$

## Step 2: Quadratic Factorization

$\\Rightarrow(2\\sec\\theta+1)(\\sec\\theta-3)=0$

$\\Rightarrow\\sec\\theta=-\\dfrac{1}{2},3$

## Step 3: Solving for Cosine

$\\Rightarrow\\cos\\theta=-2,\\dfrac{1}{3}$

$\\Rightarrow\\cos\\theta=\\dfrac{1}{3}$

## Step 4: Final Evaluation

For 7 solutions $n=13$
""",
    "c8f1886a-dc1a-4d33-afcb-5fbda9f81cd1": """<!-- paper-ocr -->

## Step 1: Simplification of LHS

$\\dfrac{3\\cos 2x+\\cos^3 2x}{\\cos^6 x-\\sin^6 x}=x^3-x^2+6$

$\\Rightarrow\\dfrac{\\cos 2x(3+\\cos^2 2x)}{\\cos 2x(1-\\sin^2 x\\cos^2 2x)}=x^3-x^2+6$

$\\Rightarrow\\dfrac{4(3+\\cos^2 2x)}{(4-\\sin^2 2x)}=x^3-x^2+6$

$\\Rightarrow\\dfrac{4(3+\\cos^2 2x)}{(3+\\cos^2 2x)}=x^3-x^2+6$

## Step 2: Solving Polynomial Equation

$x^3-x^2+2=0\\Rightarrow(x+1)(x^2-2x+2)=0$

## Step 3: Final Evaluation

so, sum of real solutions $=-1$
""",
    "c5a7e149-6dba-4275-b27d-7fbd53a76a7c": """<!-- paper-ocr -->

## Step 1: Equation Simplification

$2\\sin^3 x+2\\sin x\\cdot\\cos^2 x+4\\sin x-4=0$

$2\\sin^3 x+2\\sin x\\cdot(1-\\sin^2 x)+4\\sin x-4=0$

$6\\sin x-4=0$

## Step 2: Solving for Sine

$\\sin x=\\dfrac{2}{3}$

$n=5$ (in the given interval)

## Step 3: Quadratic Equation Solving

$x^2+5x+2=0$

$x=\\dfrac{-5\\pm\\sqrt{17}}{2}$
""",
    "30ca4295-f730-4ba5-981c-0b9028933cc1": """<!-- paper-ocr -->

## Step 1: Substitution and Quadratic Equation

Given,

$9^{1-\\tan^2 x}+9^{\\tan^2 x}=10$

Now let $9^{\\tan^2 x}=t$, then above equation will be,

$\\dfrac{9}{t}+t=10$

$\\Rightarrow t^2-10t+9=0$

$\\Rightarrow t=9$ or $t=1$

## Step 2: Solving for x

So, when $9^{\\tan^2 x}=9\\Rightarrow\\tan^2 x=1$

$\\Rightarrow\\tan x=\\pm 1\\Rightarrow x=\\pm\\dfrac{\\pi}{4}$, as given $x\\in\\left(-\\dfrac{\\pi}{2},\\dfrac{\\pi}{2}\\right)$

Now when $9^{\\tan^2 x}=1$

$\\Rightarrow\\tan^2 x=0\\Rightarrow x=0$

## Step 3: Summation Calculation

Hence, $\\beta=\\sum_{x\\in S}\\tan^2\\left(\\dfrac{x}{3}\\right)=\\tan^2\\left(\\dfrac{0}{3}\\right)+\\tan^2\\left(\\dfrac{\\pi}{12}\\right)+\\tan^2\\left(\\dfrac{-\\pi}{12}\\right)$

$=0+2(2-\\sqrt{3})^2$

$=14-8\\sqrt{3}$

## Step 4: Final Evaluation

So, the value of $\\dfrac{1}{6}(\\beta-14)^2=\\dfrac{64\\times 3}{6}=32$

Hence this is the correct option.
""",
    "73ca1a38-3c22-4848-804d-e9f83cf2599b": """<!-- paper-ocr -->

## Step 1: Trigonometric Substitution

$4\\sin^2 x-4\\cos^3 x+9-4\\cos x=0$; $x\\in[-2\\pi,2\\pi]$

$4-4\\cos^2 x-4\\cos^3 x+9-4\\cos x=0$

## Step 2: Equation Simplification

$4\\cos^3 x+4\\cos^2 x+4\\cos x-13=0$

$4\\cos^3 x+4\\cos^2 x+4\\cos x=13$

## Step 3: Range Analysis

L.H.S. $\\le 12$ can't be equal to 13.
""",
}


def main() -> int:
    sb = p.supabase_client()
    for qid, md in PACKETS.items():
        sb.table("pyq_questions").update({"solution_md": md.strip() + "\n"}).eq("id", qid).execute()
        print("updated", qid[:8], "chars", len(md), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
