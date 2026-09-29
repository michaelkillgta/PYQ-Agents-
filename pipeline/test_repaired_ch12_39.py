import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
from agents.katex_check import katex_render_ok, is_solver_dump

REPAIRS_CH12 = {
    17: {
        "format": "mcq",
        "body": "Let $A = \\{-2, -1, 0, 1, 2, 3\\}$. Let $R$ be a relation on $A$ defined by $xRy$ if and only if $y = \\max\\{x, 1\\}$. Let $l$ be the number of elements in $R$. Let $m$ and $n$ be the minimum number of elements required to be added in $R$ to make it reflexive and symmetric relations, respectively. Then $l + m + n$ is equal to",
        "options": ["12", "11", "13", "14"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    20: {
        "format": "mcq",
        "body": "Let $A = \\{2, 3, 6, 8, 9, 11\\}$ and $B = \\{1, 4, 5, 10, 15\\}$. Let $R$ be a relation on $A \\times B$ defined by $(a, b)R(c, d)$ if and only if $3ad - 7bc$ is an even integer. Then the relation $R$ is",
        "options": [
            "an equivalence relation.",
            "reflexive and symmetric but not transitive.",
            "transitive but not symmetric.",
            "reflexive but not symmetric.",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    21: {
        "format": "mcq",
        "body": "Let $S = \\{1, 2, 3, \\dots, 10\\}$. Suppose $M$ is the set of all the subsets of $S$, then the relation $R = \\{(A, B) : A \\cap B \\ne \\emptyset; A, B \\in M\\}$ is :",
        "options": [
            "symmetric and reflexive only",
            "reflexive only",
            "symmetric and transitive only",
            "symmetric only",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    23: {
        "format": "numerical",
        "body": "Let $A = \\{1, 2, 3, 4\\}$ and $R = \\{(1, 2), (2, 3), (1, 4)\\}$ be a relation on $A$. Let $S$ be the equivalence relation on $A$ such that $R \\subset S$ and the number of elements in $S$ is $n$. Then, the minimum value of $n$ is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "16",
    },
    25: {
        "format": "mcq",
        "body": "Let $A = \\{1, 2, 3, 4, 5, 6, 7\\}$. Then the relation $R = \\{(x, y) \\in A \\times A : x + y = 7\\}$ is",
        "options": [
            "an equivalence relation",
            "symmetric but neither reflexive nor transitive",
            "transitive but neither symmetric nor reflexive",
            "reflexive but neither symmetric nor transitive",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    26: {
        "format": "mcq",
        "body": "Let $R = \\{(P, Q) : P \\text{ and } Q \\text{ are at the same distance from the origin}\\}$ be a relation, then the equivalence class of $(1, -1)$ is the set",
        "options": [
            "$S = \\{(x, y) : x^2 + y^2 = 1\\}$",
            "$S = \\{(x, y) : x^2 + y^2 = 2\\}$",
            "$S = \\{(x, y) : x^2 + y^2 = \\sqrt{2}\\}$",
            "$S = \\{(x, y) : x^2 + y^2 = 4\\}$",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    29: {
        "format": "mcq",
        "body": "In a group of 100 persons, 75 speak English and 40 speak Hindi. Each person speaks at least one of the two languages. If the number of persons who speak only English is $\\alpha$ and the number of persons who speak only Hindi is $\\beta$, then the eccentricity of the ellipse $25(\\beta^2 x^2 + \\alpha^2 y^2) = \\alpha^2 \\beta^2$ is",
        "options": [
            "$\\frac{\\sqrt{119}}{12}$",
            "$\\frac{\\sqrt{117}}{12}$",
            "$\\frac{3\\sqrt{15}}{12}$",
            "$\\frac{\\sqrt{129}}{12}$",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
    30: {
        "format": "mcq",
        "body": "Let $A = \\{1, 2, 3, \\dots, 10\\}$ and $R$ be a relation on $A$ such that $R = \\{(a, b) : a = 2b + 1\\}$. Let $(a_1, a_2), (a_2, a_3), (a_3, a_4), \\dots, (a_k, a_{k+1})$ be a sequence of $k$ elements of $R$ such that the second entry of an ordered pair is equal to the first entry of the next ordered pair. Then the largest integer $k$, for which such a sequence exists, is equal to :",
        "options": ["6", "7", "5", "8"],
        "correct_option": 3,
        "numerical_answer": None,
    },
    31: {
        "format": "mcq",
        "body": "Let $A = \\{1, 2, 3, \\dots, 10\\}$ and $B = \\left\\{\\frac{m}{n} : m, n \\in A, m < n \\text{ and } \\gcd(m, n) = 1\\right\\}$. Then $n(B)$ is equal to :",
        "options": ["36", "31", "37", "29"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    32: {
        "format": "mcq",
        "body": "Let $A = \\{(x, y) \\in \\mathbb{R} \\times \\mathbb{R} : |x + y| \\ge 3\\}$ and $B = \\{(x, y) \\in \\mathbb{R} \\times \\mathbb{R} : |x| + |y| \\le 3\\}$. If $C = \\{(x, y) \\in A \\cap B : x = 0 \\text{ or } y = 0\\}$, then $\\sum_{(x, y) \\in C} |x + y|$ is :",
        "options": ["15", "24", "18", "12"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    33: {
        "format": "numerical",
        "body": "Let $S = \\{p_1, p_2, \\dots, p_{10}\\}$ be the set of first ten prime numbers. Let $A = S \\cup P$, where $P$ is the set of all possible products of distinct elements of $S$. Then the number of all ordered pairs $(x, y)$, $x \\in S, y \\in A$, such that $x$ divides $y$, is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "5120",
    },
    34: {
        "format": "mcq",
        "body": "Let $A = \\left\\{x \\in (0, \\pi) - \\left\\{\\frac{\\pi}{2}\\right\\} : \\log_{(2/\\pi)} |\\sin x| + \\log_{(2/\\pi)} |\\cos x| = 2\\right\\}$ and $B = \\{x \\ge 0 : \\sqrt{x}(\\sqrt{x} - 4) - 3|\\sqrt{x} - 2| + 6 = 0\\}$. Then $n(A \\cup B)$ is equal to :",
        "options": ["4", "8", "6", "2"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    35: {
        "format": "mcq",
        "body": "Let $S = \\mathbb{N} \\cup \\{0\\}$. Define a relation $R$ from $S$ to $\\mathbb{R}$ by $R = \\left\\{(x, y) : \\log_e y = x \\log_e\\left(\\frac{2}{5}\\right), x \\in S, y \\in \\mathbb{R}\\right\\}$. Then, the sum of all the elements in the range of $R$ is equal to :",
        "options": ["\\frac{10}{9}", "\\frac{3}{2}", "\\frac{5}{2}", "\\frac{5}{3}"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    37: {
        "format": "numerical",
        "body": "Let $A = \\{1, 2, 3, \\dots, 100\\}$. Let $R$ be a relation on $A$ defined by $(x, y) \\in R$ if and only if $2x = 3y$. Let $R_1$ be a symmetric relation on $A$ such that $R \\subset R_1$ and the number of elements in $R_1$ is $n$. Then the minimum value of $n$ is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "66",
    },
    38: {
        "format": "numerical",
        "body": "Let $A = \\{1, 2, 3, \\dots, 20\\}$. Let $R_1$ and $R_2$ be two relations on $A$ such that $R_1 = \\{(a, b) : b \\text{ is divisible by } a\\}$ and $R_2 = \\{(a, b) : a \\text{ is an integral multiple of } b\\}$. Then, the number of elements in $R_1 - R_2$ is equal to _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "46",
    },
    39: {
        "format": "numerical",
        "body": "Let $A = \\{1, 2, 3, 4, \\dots, 10\\}$ and $B = \\{0, 1, 2, 3, 4\\}$. The number of elements in the relation $R = \\{(a, b) \\in A \\times A : 2(a - b)^2 + 3(a - b) \\in B\\}$ is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "18",
    },
    41: {
        "format": "mcq",
        "body": "Let $A = \\{2, 3, 4\\}$ and $B = \\{8, 9, 12\\}$. Then the number of elements in the relation $R = \\{((a_1, b_1), (a_2, b_2)) \\in (A \\times B) \\times (A \\times B) : a_1 \\text{ divides } b_2 \\text{ and } a_2 \\text{ divides } b_1\\}$ is",
        "options": ["36", "24", "18", "12"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    42: {
        "format": "numerical",
        "body": "Let $A = \\{1, 2, 3, 4\\}$ and $R$ be a relation on the set $A \\times A$ defined by $R = \\{((a, b), (c, d)) : 2a + 3b = 4c + 5d\\}$. Then the number of elements in $R$ is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "6",
    },
    43: {
        "format": "numerical",
        "body": "Let $A = \\{1, 2, 3, 4, 5, 6, 7\\}$. Define $B = \\{T \\subseteq A : \\text{either } 1 \\notin T \\text{ or } 2 \\in T\\}$ and $C = \\{T \\subseteq A : \\text{the sum of all the elements of } T \\text{ is a prime number}\\}$. Then the number of elements in the set $B \\cup C$ is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "107",
    },
    44: {
        "format": "numerical",
        "body": "Let $A = \\{1, 2, 3, 4, 5, 6, 7\\}$ and $B = \\{3, 6, 7, 9\\}$. Then the number of elements in the set $\\{C \\subseteq A : C \\cap B \\ne \\emptyset\\}$ is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "112",
    },
    45: {
        "format": "numerical",
        "body": "Let $A = \\{n \\in \\mathbb{N} : n^2 \\le n + 10000\\}$, $B = \\{3k + 1 : k \\in \\mathbb{N}\\}$ and $C = \\{2k : k \\in \\mathbb{N}\\}$, then the sum of all the elements of the set $A \\cap (B - C)$ is equal to _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "832",
    },
    46: {
        "format": "mcq",
        "body": "Let $A = \\{2, 3, 4, 5, \\dots, 30\\}$ and $\\simeq$ be an equivalence relation on $A \\times A$, defined by $(a, b) \\simeq (c, d)$ if and only if $ad = bc$. Then the number of ordered pairs which satisfy this equivalence relation with ordered pair $(4, 3)$ is equal to :",
        "options": ["5", "6", "8", "7"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    48: {
        "format": "mcq",
        "body": "Let $A$ be the set of all functions $f : \\mathbb{Z} \\to \\mathbb{Z}$ and $R$ be a relation on $A$ such that $R = \\{(f, g) : f(0) = g(1) \\text{ and } f(1) = g(0)\\}$. Then $R$ is :",
        "options": [
            "Symmetric and transitive but not reflexive",
            "Symmetric but neither reflexive nor transitive",
            "Reflexive but neither symmetric nor transitive",
            "Transitive but neither reflexive nor symmetric",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    49: {
        "format": "mcq",
        "body": "Let $A = \\{-3, -2, -1, 0, 1, 2, 3\\}$. Let $R$ be a relation on $A$ defined by $xRy$ if and only if $0 \\le x^2 + 2y \\le 4$. Let $l$ be the number of elements in $R$ and $m$ be the minimum number of elements required to be added in $R$ to make it a reflexive relation. Then $l + m$ is equal to",
        "options": ["19", "20", "17", "18"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    50: {
        "format": "mcq",
        "body": "Let $A = \\{-3, -2, -1, 0, 1, 2, 3\\}$ and $R$ be a relation on $A$ defined by $xRy$ if and only if $2x - y \\in \\{0, 1\\}$. Let $l$ be the number of elements in $R$. Let $m$ and $n$ be the minimum number of elements required to be added in $R$ to make it reflexive and symmetric relations, respectively. Then $l + mn$ is equal to :",
        "options": ["18", "17", "15", "16"],
        "correct_option": 2,
        "numerical_answer": None,
    },
    51: {
        "format": "numerical",
        "body": "The number of relations on the set $A = \\{1, 2, 3\\}$ containing at most 6 elements including $(1, 2)$, which are reflexive and transitive but not symmetric, is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "5",
    },
    52: {
        "format": "mcq",
        "body": "Let $A = \\{0, 1, 2, 3, 4, 5\\}$. Let $R$ be a relation on $A$ defined by $(x, y) \\in R$ if and only if $\\max\\{x, y\\} \\in \\{3, 4\\}$. Then among the statements $(S_1)$ : The number of elements in $R$ is 18, and $(S_2)$ : The relation $R$ is symmetric but neither reflexive nor transitive :",
        "options": [
            "both are true",
            "both are false",
            "only ($S_2$) is true",
            "only ($S_1$) is true",
        ],
        "correct_option": 3,
        "numerical_answer": None,
    },
    53: {
        "format": "numerical",
        "body": "Let $A = \\{1, 2, 3\\}$. The number of relations on $A$, containing $(1, 2)$ and $(2, 3)$, which are reflexive and transitive but not symmetric, is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "3",
    },
    54: {
        "format": "mcq",
        "body": "Let $X = \\mathbb{R} \\times \\mathbb{R}$. Define a relation $R$ on $X$ as : $(a_1, b_1) R (a_2, b_2) \\iff b_1 = b_2$.\n\nStatement I : $R$ is an equivalence relation.\n\nStatement II : For some $(a, b) \\in X$, the set $S = \\{(x, y) \\in X : (x, y) R (a, b)\\}$ represents a line parallel to $y = x$.\n\nIn the light of the above statements, choose the correct answer from the options given below :",
        "options": [
            "Both Statement I and Statement II are false",
            "Statement I is true but Statement II is false",
            "Both Statement I and Statement II are true",
            "Statement I is false but Statement II is true",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    55: {
        "format": "mcq",
        "body": "The relation $R = \\{(x, y) : x, y \\in \\mathbb{Z} \\text{ and } x + y \\text{ is even}\\}$ is :",
        "options": [
            "reflexive and symmetric but not transitive",
            "an equivalence relation",
            "symmetric and transitive but not reflexive",
            "reflexive and transitive but not symmetric",
        ],
        "correct_option": 2,
        "numerical_answer": None,
    },
    56: {
        "format": "mcq",
        "body": "Let the relations $R_1$ and $R_2$ on the set $X = \\{1, 2, 3, \\dots, 20\\}$ be given by $R_1 = \\{(x, y) : 2x - 3y = 2\\}$ and $R_2 = \\{(x, y) : -5x + 4y = 0\\}$. If $M$ and $N$ be the minimum number of elements required to be added in $R_1$ and $R_2$, respectively, in order to make the relations symmetric, then $M + N$ equals",
        "options": ["12", "16", "8", "10"],
        "correct_option": 4,
        "numerical_answer": None,
    },
    57: {
        "format": "mcq",
        "body": "Let $A = \\{1, 2, 3, 4, 5\\}$. Let $R$ be a relation on $A$ defined by $xRy$ if and only if $4x \\le 5y$. Let $m$ be the number of elements in $R$ and $n$ be the minimum number of elements from $A \\times A$ that are required to be added to $R$ to make it a symmetric relation. Then $m + n$ is equal to :",
        "options": ["25", "24", "26", "23"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    59: {
        "format": "numerical",
        "body": "The number of relations, on the set $\\{1, 2, 3\\}$ containing $(1, 2)$ and $(2, 3)$ which are reflexive and transitive but not symmetric, is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "4",
    },
    74: {
        "format": "mcq",
        "body": "If $R = \\{(x, y) : x, y \\in \\mathbb{Z}, x^2 + 3y^2 \\le 8\\}$ is a relation on the set of integers $\\mathbb{Z}$, then the domain of $R^{-1}$ is :",
        "options": [
            "\\{-2, -1, 1, 2\\}",
            "\\{0, 1\\}",
            "\\{-2, -1, 0, 1, 2\\}",
            "\\{-1, 0, 1\\}",
        ],
        "correct_option": 4,
        "numerical_answer": None,
    },
    78: {
        "format": "mcq",
        "body": "Let the set $S = \\{2, 4, 8, 16, \\dots, 512\\}$ be partitioned into 3 sets $A, B, C$ with equal number of elements such that $A \\cup B \\cup C = S$ and $A \\cap B = B \\cap C = A \\cap C = \\emptyset$. The maximum number of such possible partitions of $S$ is equal to :",
        "options": ["1680", "1640", "1520", "1710"],
        "correct_option": 1,
        "numerical_answer": None,
    },
    80: {
        "format": "numerical",
        "body": "Let $A = \\{n \\in \\mathbb{N} : \\operatorname{HCF}(n, 45) = 1\\}$ and let $B = \\{2k : k \\in \\{1, 2, \\dots, 100\\}\\}$. Then the sum of all the elements of $A \\cap B$ is _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "5264",
    },
    83: {
        "format": "numerical",
        "body": "Let $A = \\{n \\in \\mathbb{N} : n \\text{ is a 3-digit number}\\}$, $B = \\{9k + 2 : k \\in \\mathbb{N}\\}$ and $C = \\{9k + l : k \\in \\mathbb{N}\\}$ for some $l$ ($0 < l < 9$). If the sum of all the elements of the set $A \\cap (B \\cup C)$ is $274 \\times 400$, then $l$ is equal to _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "5",
    },
    85: {
        "format": "numerical",
        "body": "Let $A = \\{0, 3, 4, 6, 7, 8, 9, 10\\}$ and $R$ be the relation defined on $A$ such that $R = \\{(x, y) \\in A \\times A : x - y \\text{ is an odd positive integer or } x - y = 2\\}$. The minimum number of elements that must be added to the relation $R$, so that it is a symmetric relation, is equal to _______.",
        "options": None,
        "correct_option": None,
        "numerical_answer": "19",
    },
    86: {
        "format": "mcq",
        "body": "Let $P(S)$ denote the power set of $S = \\{1, 2, 3, \\dots, 10\\}$. Define the relations $R_1$ and $R_2$ on $P(S)$ as $A R_1 B$ if $(A \\cap B^c) \\cup (B \\cap A^c) = \\emptyset$ and $A R_2 B$ if $A \\cup B^c = B \\cup A^c$, $\\forall A, B \\in P(S)$. Then :",
        "options": [
            "both $R_1$ and $R_2$ are equivalence relations",
            "only $R_1$ is an equivalence relation",
            "only $R_2$ is an equivalence relation",
            "both $R_1$ and $R_2$ are not equivalence relations",
        ],
        "correct_option": 1,
        "numerical_answer": None,
    },
}

def validate_repairs():
    print(f"Validating {len(REPAIRS_CH12)} repaired questions...")
    clean = True
    for qno, d in sorted(REPAIRS_CH12.items()):
        body = d["body"]
        fmt = d["format"]
        opts = d.get("options")
        
        # 1. KaTeX body
        if not katex_render_ok(body):
            print(f"FAILED KaTeX body: Q{qno}")
            clean = False
        # 2. Dump body
        if is_solver_dump(body):
            print(f"FAILED Solver dump: Q{qno}")
            clean = False
        # 3. Format check
        if fmt == "mcq":
            if not opts or len(opts) != 4:
                print(f"FAILED MCQ opts count: Q{qno} (has {len(opts) if opts else 0})")
                clean = False
            for i, opt in enumerate(opts):
                if not katex_render_ok(opt):
                    print(f"FAILED KaTeX opt {i+1}: Q{qno} -> {opt}")
                    clean = False
            if d.get("correct_option") not in [1, 2, 3, 4]:
                print(f"FAILED correct_option: Q{qno} -> {d.get('correct_option')}")
                clean = False
        elif fmt == "numerical":
            if not d.get("numerical_answer"):
                print(f"FAILED missing numerical_answer: Q{qno}")
                clean = False
            if opts is not None and len(opts) > 0:
                print(f"FAILED numerical has options: Q{qno}")
                clean = False
                
        # 4. Check for overlay text
        for token in ["mathongo", "mi", "∣∣", "\\underline"]:
            if re.search(r"\b" + re.escape(token) + r"\b", body, re.I):
                print(f"WARNING: possible overlay token '{token}' in Q{qno}")
                
    if clean:
        print("ALL 39 REPAIRS PASSED ALL QUALITY & KATEX CHECKS!")
    return clean

if __name__ == "__main__":
    validate_repairs()
