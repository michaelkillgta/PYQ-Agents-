import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

from agents.katex_check import katex_render_ok, is_solver_dump
from audit_paper_text import flags_for

REPAIRS_CH9 = {
    7: {
        "format": "mcq",
        "body": "Let $A = [a_{ij}]$ be a matrix of order $3 \\times 3$, with $a_{ij} = (\\sqrt{2})^{i+j}$. If the sum of all the elements in the third row of $A^2$ is $\\alpha + \\beta\\sqrt{2}, \\alpha, \\beta \\in \\mathbb{Z}$, then $\\alpha + \\beta$ is equal to:",
        "options": ["280", "224", "210", "168"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    14: {
        "format": "mcq",
        "body": "Let $A = \\begin{bmatrix} 0 & 2q & r \\\\ p & q & -r \\\\ p & -q & r \\end{bmatrix}$. If $AA^T = I_3$, then $|p|$ is:",
        "options": ["$\\frac{1}{\\sqrt{5}}$", "$\\frac{1}{\\sqrt{3}}$", "$\\frac{1}{\\sqrt{2}}$", "$\\frac{1}{\\sqrt{6}}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    15: {
        "format": "mcq",
        "body": "For a $3 \\times 3$ matrix $M$, let $\\text{trace}(M)$ denote the sum of all the diagonal elements of $M$. Let $A$ be a $3 \\times 3$ matrix such that $|A| = \\frac{1}{2}$ and $\\text{trace}(A) = 3$. If $B = \\operatorname{adj}(\\operatorname{adj}(2A))$, then the value of $|B| + \\text{trace}(B)$ equals:",
        "options": ["56", "132", "174", "280"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    18: {
        "format": "numerical",
        "body": "Let $A = [a_{ij}]$ be a $3 \\times 3$ matrix, where\n\n$a_{ij} = \\begin{cases} (-1)^{j-i} & \\text{if } i < j \\\\ 2 & \\text{if } i = j \\\\ (-1)^{i+j} & \\text{if } i > j \\end{cases}$\n\nthen $\\det(3 \\operatorname{adj}(2A^{-1}))$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "108",
    },
    20: {
        "format": "mcq",
        "body": "Let $A$ be a $3 \\times 3$ matrix such that $\\operatorname{adj} A = \\begin{bmatrix} 2 & -1 & 1 \\\\ -1 & 0 & 2 \\\\ 1 & -2 & -1 \\end{bmatrix}$ and $B = \\operatorname{adj}(\\operatorname{adj} A)$. If $|A| = \\lambda$ and $|(B^{-1})^T| = \\mu$, then the ordered pair $(|\\lambda|, \\mu)$ is equal to:",
        "options": ["$(3, \\frac{1}{81})$", "$(9, \\frac{1}{9})$", "$(3, 81)$", "$(9, \\frac{1}{81})$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    31: {
        "format": "mcq",
        "body": "Let $\\alpha\\beta \\ne 0$ and $A = \\begin{bmatrix} \\beta & \\alpha & 3 \\\\ \\alpha & \\alpha & \\beta \\\\ -\\beta & \\alpha & 2\\alpha \\end{bmatrix}$. If $B = \\begin{bmatrix} 3\\alpha & -9 & 3\\alpha \\\\ -\\alpha & 7 & -2\\alpha \\\\ -2\\alpha & 5 & -2\\beta \\end{bmatrix}$ is the matrix of cofactors of the elements of $A$, then $\\det(AB)$ is equal to:",
        "options": ["64", "216", "343", "125"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    49: {
        "format": "mcq",
        "body": "If $A$ is a symmetric matrix and $B$ is a skew-symmetric matrix such that $A + B = \\begin{bmatrix} 2 & 3 \\\\ 5 & -1 \\end{bmatrix}$, then $AB$ is equal to:",
        "options": [
            "$\\begin{bmatrix} -4 & 2 \\\\ 1 & 4 \\end{bmatrix}$",
            "$\\begin{bmatrix} 4 & -2 \\\\ 1 & -4 \\end{bmatrix}$",
            "$\\begin{bmatrix} 4 & -2 \\\\ -1 & -4 \\end{bmatrix}$",
            "$\\begin{bmatrix} -4 & -2 \\\\ -1 & 4 \\end{bmatrix}$"
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    54: {
        "format": "numerical",
        "body": "Let $S = \\{m \\in \\mathbb{Z} : A^{m^2} + A^m = 3I - A^{-6}\\}$, where $A = \\begin{bmatrix} 2 & -1 \\\\ 1 & 0 \\end{bmatrix}$. Then $n(S)$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    59: {
        "format": "numerical",
        "body": "Let $A = I_2 - 2MM^T$, where $M$ is a real matrix of order $2 \\times 1$ such that the relation $M^TM = I_1$ holds. If $\\lambda$ is a real number such that the relation $AX = \\lambda X$ holds for some non-zero real matrix $X$ of order $2 \\times 1$, then the sum of squares of all possible values of $\\lambda$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    62: {
        "format": "numerical",
        "body": "Let $A = \\begin{bmatrix} 0 & 1 & 2 \\\\ a & 0 & 3 \\\\ 1 & c & 0 \\end{bmatrix}$, where $a, c \\in \\mathbb{R}$. If $A^3 = A$ and the positive value of $a$ belongs to the interval $(n - 1, n]$, where $n \\in \\mathbb{N}$, then $n$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    70: {
        "format": "numerical",
        "body": "Let $A = \\begin{bmatrix} 1 & -1 \\\\ 2 & \\alpha \\end{bmatrix}$ and $B = \\begin{bmatrix} \\beta & 1 \\\\ 1 & 0 \\end{bmatrix}, \\alpha, \\beta \\in \\mathbb{R}$. Let $\\alpha_1$ be the value of $\\alpha$ which satisfies $(A + B)^2 = A^2 + \\begin{bmatrix} 2 & 2 \\\\ 2 & 2 \\end{bmatrix}$ and $\\alpha_2$ be the value of $\\alpha$ which satisfies $(A + B)^2 = B^2$. Then $|\\alpha_1 - \\alpha_2|$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    74: {
        "format": "numerical",
        "body": "Let $M = \\begin{bmatrix} 0 & -\\alpha \\\\ \\alpha & 0 \\end{bmatrix}$, where $\\alpha$ is a non-zero real number and $N = \\sum_{k=1}^{49} M^{2k}$. If $(I - M^2)N = -2I$, then the positive integral value of $\\alpha$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "1",
    },
    75: {
        "format": "mcq",
        "body": "Let $A = \\begin{bmatrix} 1 & 0 & 0 \\\\ 0 & 1 & 1 \\\\ 1 & 0 & 0 \\end{bmatrix}$. Then $A^{2025} - A^{2020}$ is equal to:",
        "options": ["$A^6 - A$", "$A^6$", "$A^5$", "$A^5 - A$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    77: {
        "format": "numerical",
        "body": "Let $S = \\left\\{ n \\in \\mathbb{N} : \\begin{bmatrix} 0 & i \\\\ 1 & 0 \\end{bmatrix}^n \\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix} = \\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}, \\forall a, b, c, d \\in \\mathbb{R} \\right\\}$, where $i = \\sqrt{-1}$. Then the number of 2-digit numbers in the set $S$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "11",
    },
    80: {
        "format": "numerical",
        "body": "Let $A = \\begin{bmatrix} a_1 \\\\ a_2 \\end{bmatrix}$ and $B = \\begin{bmatrix} b_1 \\\\ b_2 \\end{bmatrix}$ be two $2 \\times 1$ matrices with real entries such that $A = XB$, where $X = \\frac{1}{\\sqrt{3}}\\begin{bmatrix} 1 & -1 \\\\ 1 & k \\end{bmatrix}$, and $k \\in \\mathbb{R}$. If $a_1^2 + a_2^2 = \\frac{2}{3}(b_1^2 + b_2^2)$ and $(k^2 + 1)b_2^2 \\ne -2b_1 b_2$, then the value of $k$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "1",
    },
    82: {
        "format": "numerical",
        "body": "Let $I$ be an identity matrix of order $2 \\times 2$ and $P = \\begin{bmatrix} 2 & -1 \\\\ 5 & -3 \\end{bmatrix}$. Then the value of $n \\in \\mathbb{N}$ for which $P^n = 5I - 8P$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "6",
    },
    84: {
        "format": "numerical",
        "body": "If the matrix $A = \\begin{bmatrix} 1 & 0 & 0 \\\\ 0 & 2 & 0 \\\\ 3 & 0 & -1 \\end{bmatrix}$ satisfies the equation $A^{20} + \\alpha A^{19} + \\beta A = \\begin{bmatrix} 1 & 0 & 0 \\\\ 0 & 4 & 0 \\\\ 0 & 0 & 1 \\end{bmatrix}$ for some real numbers $\\alpha$ and $\\beta$, then $\\beta - \\alpha$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    85: {
        "format": "mcq",
        "body": "Let $P = \\begin{bmatrix} 1 & 2 & 1 \\\\ -2 & 3 & -4 \\\\ 1 & 9 & -1 \\end{bmatrix}$ and let $A = \\{X = (x, y, z)^T : PX = 0 \\text{ and } x^2 + y^2 + z^2 = 1\\}$, then the set $A$:",
        "options": [
            "Is a singleton.",
            "Is an empty set.",
            "Contains more than two elements.",
            "Contains exactly two elements."
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    86: {
        "format": "mcq",
        "body": "Let $a, b, c \\in \\mathbb{R}$ be all non-zero and satisfy $a^3 + b^3 + c^3 = 2$. If the matrix $A = \\begin{bmatrix} a & b & c \\\\ b & c & a \\\\ c & a & b \\end{bmatrix}$ satisfies $A^T A = I$, then a value of $abc$ can be:",
        "options": ["$-\\frac{1}{3}$", "$\\frac{1}{3}$", "3", "$\\frac{2}{3}$"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    90: {
        "format": "mcq",
        "body": "The total number of matrices $A = \\begin{bmatrix} 0 & 2y & 1 \\\\ 2x & y & -1 \\\\ 2x & -y & 1 \\end{bmatrix}, (x, y \\in \\mathbb{R}, x \\ne y)$ for which $A^T A = 3I_3$ is:",
        "options": ["6", "3", "4", "2"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    115: {
        "format": "mcq",
        "body": "Let $A$ be a $3 \\times 3$ invertible matrix. If $|\\operatorname{adj}(24A)| = |\\operatorname{adj}(3\\operatorname{adj}(2A))|$, then $|A|^2$ is equal to:",
        "options": ["$2^6$", "$2^{12}$", "$5^{12}$", "$6^6$"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    150: {
        "format": "mcq",
        "body": "Let $S = \\{\\sqrt{n} : 1 \\le n \\le 50 \\text{ and } n \\text{ is odd}\\}$. Let $a \\in S$ and $A = \\begin{bmatrix} 1 & 0 & a \\\\ -1 & 1 & 0 \\\\ -a & 0 & 1 \\end{bmatrix}$. If $\\sum_{a \\in S} \\det(\\operatorname{adj} A) = 100\\lambda$, then $\\lambda$ is equal to:",
        "options": ["218", "221", "663", "1717"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    153: {
        "format": "numerical",
        "body": "Let $P = \\begin{bmatrix} -30 & 20 & 56 \\\\ 90 & 140 & 112 \\\\ 120 & 60 & 14 \\end{bmatrix}$ and $A = \\begin{bmatrix} 2 & 7 & \\omega^2 \\\\ -1 & -\\omega & 1 \\\\ 0 & -\\omega & -\\omega + 1 \\end{bmatrix}$, where $\\omega = \\frac{-1 + i\\sqrt{3}}{2}$, and $I_3$ be the identity matrix of order 3. If the determinant of the matrix $(P^{-1}AP - I_3)^2$ is $\\alpha\\omega^2$, then the value of $\\alpha$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "36",
    },
}

all_ok = True
for q, data in sorted(REPAIRS_CH9.items()):
    body = data["body"]
    opts = data["options"]
    fmt = data["format"]
    
    if not katex_render_ok(body):
        print(f"FAIL Q{q} body KaTeX: {body}")
        all_ok = False
        
    if opts:
        for i, opt in enumerate(opts, start=1):
            if not katex_render_ok(opt):
                print(f"FAIL Q{q} opt{i} KaTeX: {opt}")
                all_ok = False
                
    if is_solver_dump(body):
        print(f"FAIL Q{q} solver dump")
        all_ok = False
        
    b_flags = flags_for(body, is_option=False)
    if b_flags:
        print(f"FAIL Q{q} body flags: {b_flags}")
        all_ok = False
    if opts:
        for i, opt in enumerate(opts, start=1):
            o_flags = flags_for(opt, is_option=True)
            blocking = [f for f in o_flags if not f.startswith("empty")]
            if blocking:
                print(f"FAIL Q{q} opt{i} flags: {blocking}")
                all_ok = False

if all_ok:
    print(f"ALL {len(REPAIRS_CH9)} QUESTIONS PASSED ALL CHECKS!")
