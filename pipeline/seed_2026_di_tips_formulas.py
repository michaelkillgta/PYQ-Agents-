#!/usr/bin/env python3
"""Fill Tips / Formula's on 2026 January Definite Integration only.

NCERT Class 12 Integrals (properties, even/odd, GIF) and NTA JEE Main wording.
Direction only — no final option or numerical key.
"""
from __future__ import annotations

import sys

import pyq_common as p

ROWS: dict[str, tuple[str, str]] = {
    "b57e742c-a524-42dc-ba28-c3cab05654cd": (
        """Limits are symmetric about $0$. Split the numerator: a constant piece and $x^{11}$.

The denominator depends on $|x|$, so it is even. $x^{11}$ is odd. Product of an odd function with an even function is odd, so that piece vanishes on $[-a,a]$ (NCERT Class 12, Integrals — properties).

The leftover integrand is even: write $I=2\\int_{0}^{\\pi/6}$. Then put $t=|x|+\\pi/6$ and use $1-\\sin t=(\\sin(t/2)-\\cos(t/2))^2$.""",
        """$\\displaystyle\\int_{-a}^{a}f(x)\\,dx=0$ if $f$ is odd, and $2\\int_{0}^{a}f(x)\\,dx$ if $f$ is even.

$|x|$ is even; $x^{11}$ is odd.

$1-\\sin t=\\bigl(\\sin\\tfrac{t}{2}-\\cos\\tfrac{t}{2}\\bigr)^2$.""",
    ),
    "40a7e886-7f4f-4da9-8d49-c61787719a81": (
        """The modulus forces you to find where $\\sin 3x+\\sin 2x+\\sin x$ changes sign in $[0,\\pi]$.

Pair $\\sin 3x+\\sin x$ first (sum-to-product), then factor $\\sin 2x$. Zeros of the product split the interval. Integrate the positive pieces separately (NCERT: $\\int|g|$ by breaking at roots).""",
        """$\\sin A+\\sin B=2\\sin\\dfrac{A+B}{2}\\cos\\dfrac{A-B}{2}$.

$\\sin 3x+\\sin x=2\\sin 2x\\cos x$.

$\\int_{a}^{b}|f|=\\sum$ signed pieces on intervals where $f$ does not change sign.""",
    ),
    "f90a4042-c434-4d5c-9029-c7939e6b09e8": (
        """Write the argument as a difference of two $\\cot^{-1}$ if a tangent-subtraction identity fits.

On $[0,1]$ use $x\\mapsto 1-x$ (NCERT: $\\int_{0}^{a}f(x)=\\int_{0}^{a}f(a-x)$). That usually pairs $\\cot^{-1}$ with $\\tan^{-1}$. Then integrate by parts or a linear substitution to reach $\\tan^{-1}2$ and $\\log 5$.""",
        """$\\int_{0}^{a}f(x)\\,dx=\\int_{0}^{a}f(a-x)\\,dx$.

$\\cot^{-1}u+\\tan^{-1}u=\\dfrac{\\pi}{2}$ for $u>0$.

$\\dfrac{d}{dx}\\cot^{-1}u=-\\dfrac{u'}{1+u^2}$.""",
    ),
    "37df45b0-8dd2-461e-ae5d-49cc2b3b4b65": (
        """$[x]$ is constant on each $[n,n+1)$. Split $[-\\pi/2,\\pi/2]$ at the integers $-1$ and $0$ (and at $-\\pi/2$).

On each slab the integrand is $1/(n+4)$, a constant. Add the lengths of those slabs (NCERT greatest-integer integrals).""",
        """$[x]=n$ for $x\\in[n,n+1)$, $n\\in\\mathbb{Z}$.

$\\int_{c}^{d}\\dfrac{dx}{n+4}=\\dfrac{d-c}{n+4}$ on a slab where $[x]=n$.""",
    ),
    "c7c03e0a-4c9f-4697-be03-1fce67a20b22": (
        """On each $[n,n+1)$, $[x]=n$ and $[x+3]=n+3$. Reduce $f$ to a quadratic in $n$.

Factor that quadratic. The question then asks where $f$ is zero / positive / an integral of $f$ — read the options and test integer $n$ only on those unit intervals.""",
        """$[x]=n$ on $[n,n+1)$.

$[x+k]=[x]+k$ for integer $k$.

$n^2-n-6=(n-3)(n+2)$.""",
    ),
    "841348f6-f9cd-4486-8937-0674b15f6422": (
        """$\\{x^{1/3}\\}=x^{1/3}-[x^{1/3}]$. Split $[0,64]$ at cubes $1,8,27,64$ so $[x^{1/3}]$ is the integer $0,1,2,3$.

After $\\alpha$ is known, the $\\theta$-integral is even about $\\pi/4$: divide by $\\cos^6\\theta$ or use $\\tan\\theta=t$. $\\sin^6+\\cos^6=1-3\\sin^2\\cos^2$.""",
        """$\\int x^{1/3}\\,dx=\\dfrac{3}{4}x^{4/3}$.

$\\sin^6\\theta+\\cos^6\\theta=1-3\\sin^2\\theta\\cos^2\\theta$.

$\\int_{0}^{\\pi/2}\\dfrac{\\sin^2\\theta}{\\sin^6\\theta+\\cos^6\\theta}\\,d\\theta$ is a standard $t=\\tan\\theta$ form.""",
    ),
    "7c14ebc2-ed05-46cf-b087-7fd7dd40f50a": (
        """Limits $\\pi/24$ and $5\\pi/24$ add to $\\pi/4$. Use $x\\mapsto \\pi/4-x$ after the inner $2x$ (so $\\tan 2x$ becomes $\\cot 2x$).

$\\sqrt[3]{\\tan}+\\sqrt[3]{\\cot}$ pairing gives $I+I=$ length of the interval. No need to expand the cube root (NCERT property $\\int_a^b f(x)=\\int_a^b f(a+b-x)$).""",
        """$\\int_{a}^{b}f(x)\\,dx=\\int_{a}^{b}f(a+b-x)\\,dx$.

$\\tan\\bigl(\\tfrac{\\pi}{2}-\\theta\\bigr)=\\cot\\theta$.

If $I=\\int_{a}^{b}\\dfrac{dx}{1+\\sqrt[3]{\\tan 2x}}$ and $a+b=\\pi/4$, then $2I=b-a$.""",
    ),
    "ba2c72af-060d-4865-86de-51e7354b56c4": (
        """The upper limit is the variable $x$. Differentiate both sides with respect to $x$ (NCERT: Leibniz / first fundamental theorem).

The left side is a convolution with $\\sin(x-t)$. After one derivative you get an ODE or an algebraic relation in $x$. Count roots of that relation in $[0,100]$.""",
        """$\\dfrac{d}{dx}\\int_{0}^{x}g(x,t)\\,dt=g(x,x)+\\int_{0}^{x}\\partial_x g(x,t)\\,dt$.

$\\int_{0}^{x}t^{2}\\sin(x-t)\\,dt$ expands by $u=x-t$.""",
    ),
    "0b3021de-4016-4f73-b456-72bc1d258b2b": (
        """Put $u=tx/36$. The left side becomes a constant times $\\int_{0}^{x}f(u)\\,du$.

Differentiate both sides (fundamental theorem) to get $f(x)$ proportional to $f'(x)$ or a linear ODE. A standard parabola means $y=ax^2+bx+c$; fit $(2,1)$ and the given $\\beta$.""",
        """$\\dfrac{d}{dx}\\int_{0}^{x}f(u)\\,du=f(x)$.

A standard parabola through the origin / vertex form is $y=ax^2$ or $y=a(x-h)^2+k$ as the options force.

If $\\int_{0}^{x}f=kx f$, then $f$ is homogeneous of degree $0$ or linear in $x$ according to $k$.""",
    ),
    "cc29f804-894e-4f37-9c0a-8b224df6762b": (
        """The integral $\\int_0^1(y+xe^{x})f(y)\\,dy$ is linear in $x$: constants $A=\\int f$ and $B=\\int y e^{y}f(y)$ (check the printed $e^{x}$ versus $e^{y}$).

Then $f(x)=e^{x}+c_1+c_2 x e^{x}$. Plug back into $A,B$ and solve the $2\\times 2$ system. Finally $e+f(0)$.""",
        """If $f(x)=g(x)+\\int_{0}^{1}K(x,y)f(y)\\,dy$ and $K$ is separable, $f$ is $g$ plus unknown constants.

$\\int_{0}^{1}e^{y}\\,dy=e-1$, $\\int_{0}^{1}ye^{y}\\,dy$ by parts.""",
    ),
    "e2fe0886-ba55-4d15-980c-fd45931073fa": (
        """$f$ is a polynomial. The identity holds for all $x$, so substitute $u=x^2+1$ (then $u\\ge 1$) and rewrite the right-hand side in $u$.

That gives $f(u)$ as a quadratic. Extend the same polynomial to $[0,3]$ and integrate term by term.""",
        """If $f(x^2+1)=x^4+5x^2+2$ and $u=x^2+1$, then $x^2=u-1$ and $f(u)=(u-1)^2+5(u-1)+2$.

$\\int_{0}^{3}(au^2+bu+c)\\,du=\\bigl[\\tfrac{a}{3}u^3+\\tfrac{b}{2}u^2+cu\\bigr]_{0}^{3}$.""",
    ),
    "885c1a0c-1480-46b3-a9be-12be02c6824a": (
        """Split the integrand into $\\csc^5 x\\sec^2 x$ minus a multiple of $\\csc^5 x$, or write everything in $\\sin$ and $\\cos$ and divide numerator and denominator by $\\cos^5 x$ to get $t=\\tan x$.

A quicker JEE route: divide num/den by $\\sin^2 x\\cos^2 x$ and use $d(\\cot)$ / $d(\\tan)$. Evaluate the antiderivative at $\\pi/6$ and $\\pi/4$ only — do not simplify the indefinite form beyond what those two points need.""",
        """$\\dfrac{1}{\\sin^5 x\\cos^2 x}=\\csc^5 x\\sec^2 x$.

$\\dfrac{d}{dx}\\cot x=-\\csc^2 x$, $\\dfrac{d}{dx}\\tan x=\\sec^2 x$.

$\\int\\csc^n$ reduction, or $t=\\tan x$ after dividing by $\\cos^n$.""",
    ),
    "219dbbf4-0155-421b-91ed-e94fe24858fb": (
        """$|\\sin\\pi x|$ has period $1$. On each $[k,k+1]$ the graph is the same hump.

$\\int_{0}^{r}x|\\sin\\pi x|\\,dx$: write $r=n+f$, sum $n$ full periods plus a leftover. Use $x\\mapsto k+u$ on the $k$-th interval. Factor $\\sqrt{\\pi}$ stays outside the sum.""",
        """$|\\sin\\pi x|$ has period $1$; $\\int_{0}^{1}|\\sin\\pi x|\\,dx=2/\\pi$.

$\\int_{k}^{k+1}x|\\sin\\pi x|\\,dx=k\\int_{0}^{1}|\\sin\\pi t|\\,dt+\\int_{0}^{1}t|\\sin\\pi t|\\,dt$.

$\\int_{0}^{1}t\\sin\\pi t\\,dt$ by parts.""",
    ),
    "bbe70f20-8456-47ce-8eb4-977ffc48c796": (
        """Split at $0$ and at $-1$ because of $[x]$. Also split where $[\\sin x]$ or $[\\cos x]$ jumps (at $0$, and where $\\sin$ or $\\cos$ hit integers, i.e. $0,\\pm 1$).

On each open slab both numerator and denominator are constants. Add $12(3+[x])/(3+[\\sin x]+[\\cos x])$ times length.""",
        """$[x]=-2$ on $[-\\pi/2,-1)$, $-1$ on $[-1,0)$, $0$ on $[0,\\pi/2]$.

$[\\sin x]\\in\\{-1,0,1\\}$, $[\\cos x]\\in\\{-1,0,1\\}$ on $[-\\pi/2,\\pi/2]$.

Constant integrand on each slab: $\\int_{c}^{d}C\\,dx=C(d-c)$.""",
    ),
}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sb = p.supabase_client()
    for qid, (tips, formulas) in ROWS.items():
        sb.table("pyq_questions").update({
            "tips_md": tips.strip(),
            "formulas_md": formulas.strip(),
        }).eq("id", qid).execute()
        print(f"ok {qid[:8]}", flush=True)
    n = len(
        sb.table("pyq_questions")
        .select("id")
        .in_("id", list(ROWS))
        .not_.is_("tips_md", "null")
        .execute()
        .data
        or []
    )
    print(f"filled {n}/{len(ROWS)}", flush=True)
    return 0 if n == len(ROWS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
