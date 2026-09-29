import json
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

from agents.katex_check import katex_render_ok, is_solver_dump
from audit_paper_text import flags_for

# Define the 18 repaired questions
REPAIRS = {
    17: {
        "format": "mcq",
        "body": "Let $S$ be the set of all values of $a_{1}$ for which the mean deviation about the mean of 100 consecutive positive integers $a_{1}, a_{2}, a_{3}, \\dots, a_{100}$ is 25. Then $S$ is:",
        "options": ["$\\phi$", "$\\{99\\}$", "$\\mathbb{N}$", "$\\{9\\}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    30: {
        "format": "mcq",
        "body": "A student scores the following marks in five tests: $45, 54, 41, 57, 43$. His score is not known for the sixth test. If the mean score is 48 in the six tests, then the standard deviation of the marks in six tests is:",
        "options": ["$\\frac{10}{3}$", "$\\frac{100}{3}$", "$\\frac{10}{\\sqrt{3}}$", "$\\frac{100}{\\sqrt{3}}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    31: {
        "format": "mcq",
        "body": "If the data $x_{1}, x_{2}, \\dots, x_{10}$ is such that the mean of first four of these is 11, the mean of the remaining six is 16 and the sum of squares of all of these is 2000, then the standard deviation of this data is:",
        "options": ["$2\\sqrt{2}$", "4", "2", "$\\sqrt{2}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    38: {
        "format": "numerical",
        "body": "Consider the following frequency distribution:\n\n\\begin{tabular}{|l|c|c|c|c|c|} \\hline Class & $0 - 6$ & $6 - 12$ & $12 - 18$ & $18 - 24$ & $24 - 30$ \\\\ \\hline Frequency & $a$ & $b$ & 12 & 9 & 5 \\\\ \\hline \\end{tabular}\n\nIf mean $= \\frac{309}{22}$ and median $= 14$, then the value of $(a - b)^2$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    45: {
        "format": "numerical",
        "body": "If the mean and variance of the data $65, 68, 58, 44, 48, 45, 60, \\alpha, \\beta, 60$ where $\\alpha > \\beta$ are $56$ and $66.2$ respectively, then $\\alpha^2 + \\beta^2$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "6344",
    },
    50: {
        "format": "mcq",
        "body": "The mean and variance of a set of 15 numbers are 12 and 14 respectively. The mean and variance of another set of 15 numbers are 14 and $\\sigma^2$ respectively. If the variance of all the 30 numbers in the two sets is 13, then $\\sigma^2$ is equal to:",
        "options": ["10", "11", "9", "12"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    57: {
        "format": "numerical",
        "body": "Let $X = \\{11, 12, 13, \\dots, 40, 41\\}$ and $Y = \\{61, 62, 63, \\dots, 90, 91\\}$ be the two sets of observations. If $\\bar{x}$ and $\\bar{y}$ are their respective means and $\\sigma^2$ is the variance of all the observations in $X \\cup Y$, then $|\\bar{x} + \\bar{y} - \\sigma^2|$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "603",
    },
    60: {
        "format": "numerical",
        "body": "The mean and standard deviation of 40 observations are 30 and 5 respectively. It was noticed that two of these observations 12 and 10 were wrongly recorded. If $\\sigma$ is the standard deviation of the data after omitting the two wrong observations from the data, then $38\\sigma^2$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "238",
    },
    73: {
        "format": "mcq",
        "body": "Let $X = \\{x \\in \\mathbb{N} : 1 \\le x \\le 17\\}$ and $Y = \\{ax + b : x \\in X \\text{ and } a, b \\in \\mathbb{R}, a > 0\\}$. If mean and variance of elements of $Y$ are 17 and 216 respectively, then $a + b$ is equal to:",
        "options": ["7", "-7", "-27", "9"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    74: {
        "format": "numerical",
        "body": "If the variance of the terms in an increasing A.P. $b_{1}, b_{2}, b_{3}, \\dots, b_{11}$ is 90, then the common difference of this A.P. is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    76: {
        "format": "numerical",
        "body": "If the variance of the following frequency distribution:\n\n\\begin{tabular}{|l|c|c|c|} \\hline Class & $10 - 20$ & $20 - 30$ & $30 - 40$ \\\\ \\hline Frequency & 2 & $x$ & 2 \\\\ \\hline \\end{tabular}\n\nis 50, then $x$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    91: {
        "format": "numerical",
        "body": "The mean of 10 numbers $7 \\times 8, 10 \\times 10, 13 \\times 12, 16 \\times 14, \\dots$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "398",
    },
    93: {
        "format": "mcq",
        "body": "Let $\\mu$ be the mean and $\\sigma$ be the standard deviation of the distribution\n\n\\begin{tabular}{|c|c|c|c|c|c|c|} \\hline $X_i$ & 0 & 1 & 2 & 3 & 4 & 5 \\\\ \\hline $f_i$ & $k + 2$ & $2k$ & $k^2 - 1$ & $k^2 - 1$ & $k^2 + 1$ & $k - 3$ \\\\ \\hline \\end{tabular}\n\nwhere $\\sum f_i = 62$. If $[x]$ denotes the greatest integer $\\le x$, then $[\\mu^2 + \\sigma^2]$ is equal to:",
        "options": ["9", "8", "7", "6"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    95: {
        "format": "numerical",
        "body": "The mean and variance of 10 observations were calculated as 15 and 15 respectively by a student who took by mistake 25 instead of 15 for one observation. Then, the correct standard deviation is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "2",
    },
    96: {
        "format": "numerical",
        "body": "Let the mean and the variance of 20 observations $x_{1}, x_{2}, \\dots, x_{20}$ be 15 and 9, respectively. For $\\alpha \\in \\mathbb{R}$, if the mean of $(x_{1} + \\alpha)^2, (x_{2} + \\alpha)^2, \\dots, (x_{20} + \\alpha)^2$ is 178, then the square of the maximum value of $\\alpha$ is equal to _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    103: {
        "format": "numerical",
        "body": "Let $X_{1}, X_{2}, \\dots, X_{18}$ be eighteen observations such that $\\sum_{i=1}^{18}(X_{i} - \\alpha) = 36$ and $\\sum_{i=1}^{18} (X_{i} - \\beta)^2 = 90$, where $\\alpha$ and $\\beta$ are distinct real numbers. If the standard deviation of these observations is 1, then the value of $|\\alpha - \\beta|$ is _________.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    105: {
        "format": "mcq",
        "body": "Let $x_{i} \\ (1 \\le i \\le 10)$ be ten observations of a random variable $X$. If $\\sum_{i=1}^{10}(x_{i} - p) = 3$ and $\\sum_{i=1}^{10}(x_{i} - p)^2 = 9$ where $0 \\ne p \\in \\mathbb{R}$, then the standard deviation of these observations is:",
        "options": ["$\\frac{4}{5}$", "$\\sqrt{\\frac{3}{5}}$", "$\\frac{9}{10}$", "$\\frac{7}{10}$"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    107: {
        "format": "mcq",
        "body": "The outcome of each of 30 items was observed; 10 items gave an outcome $\\frac{1}{2} - d$ each, 10 items gave outcome $\\frac{1}{2}$ each and the remaining 10 items gave outcome $\\frac{1}{2} + d$ each. If the variance of this outcome data is $\\frac{4}{3}$, then $|d|$ equals:",
        "options": ["$\\frac{2}{3}$", "2", "$\\frac{\\sqrt{5}}{2}$", "$\\sqrt{2}$"],
        "correct_option": 4,
        "numerical_answer": None,
    },
}

all_ok = True
for q, data in sorted(REPAIRS.items()):
    body = data["body"]
    opts = data["options"]
    fmt = data["format"]
    
    # 1. KaTeX check
    k_ok = katex_render_ok(body)
    if not k_ok:
        print(f"FAIL Q{q} body KaTeX: {body}")
        all_ok = False
        
    if opts:
        for i, opt in enumerate(opts, start=1):
            if not katex_render_ok(opt):
                print(f"FAIL Q{q} opt{i} KaTeX: {opt}")
                all_ok = False
                
    # 2. Solver dump check
    if is_solver_dump(body):
        print(f"FAIL Q{q} solver dump")
        all_ok = False
        
    # 3. Audit text flags
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
    print("ALL 18 QUESTIONS PASSED ALL CHECKS!")
