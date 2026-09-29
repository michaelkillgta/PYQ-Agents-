#!/usr/bin/env python3
"""Shared helpers for the PYQ ingestion pipeline (Phases 2-9)."""
import base64
import hashlib
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx
from supabase import create_client

from agents.models import IMAGE_MODELS

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
PDF_PATH = r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Physics.pdf"

CHAPTER_5 = 5
CHAPTER_5_PAGES = range(47, 61)          # 14 pages that carry Laws of Motion questions
BUCKET = "pyq"
FIGURE_PREFIX = "physics/figures"

BOOKS = {
    "physics": {
        "out": ROOT / "out",
        "figure_prefix": "physics/figures",
        "subject_name": "Physics",
        "pdf": r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Physics.pdf",
    },
    "math": {
        "out": ROOT / "out-math",
        "figure_prefix": "math/figures",
        "subject_name": "Mathematics",
        "pdf": r"C:\Users\tempo\Downloads\MathonGo PYQ Book (JEE Main 2025 - 2019) - Mathematics.pdf",
    },
}


def configure_book(book: str) -> dict:
    """Point OUT / figures / PDF at Physics or Mathematics. Never mix caches."""
    spec = BOOKS.get(book)
    if spec is None:
        raise ValueError(f"unknown book {book!r}")
    global OUT, FIGURE_PREFIX, PDF_PATH
    OUT = spec["out"]
    FIGURE_PREFIX = spec["figure_prefix"]
    PDF_PATH = spec["pdf"]
    return spec


def resolve_chapter_id(sb, chapter_no: int, subject_name: str):
    """chapter_no is per PDF book. Physics and Maths both have a chapter 1."""
    sid = sb.table("pyq_subjects").select("id").eq("name", subject_name).execute().data[0]["id"]
    unit_ids = [u["id"] for u in sb.table("pyq_units").select("id").eq("subject_id", sid).execute().data]
    rows = (sb.table("pyq_chapters").select("id")
            .eq("chapter_no", chapter_no)
            .in_("unit_id", unit_ids)
            .execute().data)
    if len(rows) != 1:
        raise RuntimeError(
            f"chapter_no={chapter_no} subject={subject_name!r} matched {len(rows)} rows"
        )
    return rows[0]["id"]

# v1 chat is text-only. Page images go through Document AI digitise, then this.
SARVAM_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_V2_CHAT_URL = "https://api.sarvam.ai/v2/chat/completions"
SARVAM_DIGITISE_URL = "https://api.sarvam.ai/doc-ai/v1/job/digitise"
SARVAM_JOB_STATUS_URL = "https://api.sarvam.ai/doc-ai/v1/job/{job_id}/status"
SARVAM_JOB_RESULTS_URL = "https://api.sarvam.ai/doc-ai/v1/job/{job_id}/results"
SARVAM_PARSE_MODEL = "sarvam-105b"
GEMINI_CHAT_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# PDF chapter number -> app catalog chapter slug (slugify() of the catalog name).
# Chapter 17 (Electrostatics) straddles two catalog chapters and is deferred.
CATALOG_SLUG = {
    1: "units-and-measurements",
    2: "units-and-measurements",
    3: "motion-in-a-straight-line",
    4: "motion-in-a-plane",
    5: "laws-of-motion",
    6: "work-energy-and-power",
    7: "system-of-particles-and-rotational-motion",
    8: "system-of-particles-and-rotational-motion",
    9: "gravitation",
    10: "mechanical-properties-of-solids",
    11: "mechanical-properties-of-fluids",
    12: "oscillations",
    13: "waves",
    14: "thermal-properties-of-matter",
    15: "thermodynamics",
    16: "kinetic-theory-of-gases",
    17: None,
    18: "electrostatic-potential-and-capacitance",
    19: "current-electricity",
    20: "magnetism-and-matter",
    21: "moving-charges-and-magnetism",
    22: "electromagnetic-induction",
    23: "alternating-current",
    24: "ray-optics",
    25: "wave-optics",
    26: "dual-nature-of-radiation-and-matter",
    27: "atoms",
    28: "nuclei",
    29: "electromagnetic-waves",
    30: "semiconductor-electronics",
    31: "communication-system",
    32: "units-and-measurements",
}

# 2025 January / April Mathematics chapter-wise bank. chapter_no matches that TOC.
MATH_2025_SESSION_CHAPTERS = [
    (1, "Basic of Mathematics", "basic-of-mathematics"),
    (2, "Quadratic Equation", "quadratic-equation"),
    (3, "Complex Number", "complex-number"),
    (4, "Sequences and Series", "sequences-and-series"),
    (5, "Permutation Combination", "permutation-combination"),
    (6, "Binomial Theorem", "binomial-theorem"),
    (7, "Statistics", "statistics"),
    (8, "Matrices", "matrices"),
    (9, "Determinants", "determinants"),
    (10, "Probability", "probability"),
    (11, "Sets and Relations", "sets-and-relations"),
    (12, "Functions", "functions"),
    (13, "Limits", "limits"),
    (14, "Continuity and Differentiability", "continuity-and-differentiability"),
    (15, "Application of Derivatives", "application-of-derivatives"),
    (16, "Indefinite Integration", "indefinite-integration"),
    (17, "Definite Integration", "definite-integration"),
    (18, "Area Under Curves", "area-under-curves"),
    (19, "Differential Equations", "differential-equations"),
    (20, "Straight Lines", "straight-lines"),
    (21, "Circle", "circle"),
    (22, "Parabola", "parabola"),
    (23, "Ellipse", "ellipse"),
    (24, "Hyperbola", "hyperbola"),
    (25, "Trigonometric Ratios & Identities", "trigonometric-ratios-and-identities"),
    (26, "Trigonometric Equations", "trigonometric-equations"),
    (27, "Inverse Trigonometric Functions", "inverse-trigonometric-functions"),
    (28, "Vector Algebra", "vector-algebra"),
    (29, "Three Dimensional Geometry", "three-dimensional-geometry"),
]


def load_env() -> dict:
    env = {}
    path = ROOT / ".env"
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    os.environ.update(env)
    return env


def supabase_client():
    env = load_env()
    url = env.get("SUPABASE_URL") or env["NEXT_PUBLIC_SUPABASE_URL"]
    key = env.get("SUPABASE_SERVICE_KEY") or env["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def load_skeleton() -> list:
    return json.loads((OUT / "skeleton.json").read_text(encoding="utf-8"))


def load_figures_manifest() -> list:
    return json.loads((OUT / "figures.json").read_text(encoding="utf-8"))


def load_answer_key() -> dict:
    return json.loads((OUT / "answer_key.json").read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


_NORM = [
    (re.compile(r"\\dfrac"), r"\\frac"),
    (re.compile(r"\\tfrac"), r"\\frac"),
    (re.compile(r"\\left\("), "("),
    (re.compile(r"\\right\)"), ")"),
    (re.compile(r"\\left\["), "["),
    (re.compile(r"\\right\]"), "]"),
    (re.compile(r"\\,|\\;|\\!|\\quad|\\qquad"), " "),
    (re.compile(r"\u2212"), "-"),
    (re.compile(r"\s+"), " "),
]


def normalise_latex(text) -> str:
    """Collapse cosmetic LaTeX differences so a diff only shows real ones."""
    if text is None:
        return ""
    s = str(text)
    for pattern, repl in _NORM:
        s = pattern.sub(repl, s)
    return s.strip()


class RateLimiter:
    """Sarvam Starter allows 60 requests per minute."""

    def __init__(self, per_minute: int = 60):
        self.interval = 60.0 / per_minute
        self.lock = threading.Lock()
        self.next_at = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            if now < self.next_at:
                time.sleep(self.next_at - now)
                now = time.monotonic()
            self.next_at = now + self.interval


def chat_content(raw: dict) -> str:
    """Sarvam-105b sometimes fills reasoning_content and leaves content null."""
    msg = ((raw.get("choices") or [{}])[0].get("message") or {})
    text = msg.get("content") or msg.get("reasoning_content") or ""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("empty model content")
    return text


def salvage_tex_json(text: str) -> str:
    """Stop json.loads from eating TeX: \\t in \\text/\\to, unknown \\int, etc."""
    def repl(m: re.Match) -> str:
        slashes, cmd = m.group(1), m.group(2)
        if len(slashes) % 2 == 0:
            return m.group(0)
        if cmd[0] == "u" and re.match(r"u[0-9a-fA-F]{4}", cmd):
            return m.group(0)
        if cmd in {"b", "f", "n", "r", "t"}:
            return m.group(0)
        return slashes + "\\" + cmd

    return re.sub(r"(\\+)([A-Za-z]+)", repl, text or "")


def parse_json_content(raw: dict) -> dict:
    text = chat_content(raw).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    blob = salvage_tex_json(text)
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        start, end = blob.find("{"), blob.rfind("}")
        if start >= 0 and end > start:
            return json.loads(blob[start:end + 1])
        raise


class WhitelistError(Exception):
    """Invariant 2: the model returned a q_no or figure_key we did not supply."""


def validate_page_response(payload: dict, allowed_q_nos: set, allowed_fig_keys: set) -> list:
    """Reject unknown q_no or figure_key. Return the validated question list."""
    questions = payload.get("questions")
    if not isinstance(questions, list):
        raise WhitelistError("response has no 'questions' list")

    got = set()
    for q in questions:
        q_no = q.get("q_no")
        if q_no not in allowed_q_nos:
            raise WhitelistError(f"unknown q_no {q_no!r}")
        got.add(q_no)
        blob = json.dumps(q, ensure_ascii=False)
        for key in re.findall(r"\[\[fig:([^\]]+)\]\]", blob):
            if key not in allowed_fig_keys:
                raise WhitelistError(f"unknown figure_key {key!r} on q_no {q_no}")

    if got != allowed_q_nos:
        missing = sorted(allowed_q_nos - got)
        extra = sorted(got - allowed_q_nos)
        raise WhitelistError(f"q_no set mismatch; missing={missing} extra={extra}")
    return questions


def digitise_page(page_no: int, api_key: str, timeout: float = 180.0) -> dict:
    """OCR one page raster via Sarvam Document AI. Cached under out/ocr/."""
    cache = OUT / "ocr" / f"page_{page_no:03d}.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    png = OUT / "pages" / f"page_{page_no:03d}.png"
    headers = {"api-subscription-key": api_key}
    r = httpx.post(
        SARVAM_DIGITISE_URL,
        headers=headers,
        files={"file": (png.name, png.read_bytes(), "image/png")},
        data={"language": "en-IN", "output_format": "md"},
        timeout=timeout,
    )
    r.raise_for_status()
    job_id = r.json()["job_id"]
    status = "pending"
    for _ in range(60):
        s = httpx.get(SARVAM_JOB_STATUS_URL.format(job_id=job_id),
                      headers=headers, timeout=60)
        s.raise_for_status()
        status = (s.json().get("status") or "").lower()
        if status in ("completed", "partially_completed", "failed", "rejected"):
            break
        time.sleep(2)
    if status not in ("completed", "partially_completed"):
        raise RuntimeError(f"digitise page {page_no} ended {status} job={job_id}")
    res = httpx.get(SARVAM_JOB_RESULTS_URL.format(job_id=job_id),
                    headers=headers, timeout=60)
    res.raise_for_status()
    payload = res.json()
    cache.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


def digitise_pages_parallel(page_nos: list, api_key: str, workers: int = 4) -> dict:
    """OCR many pages. Cache hits skip the network. Failures are error strings."""
    results: dict = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(digitise_page, n, api_key): n for n in page_nos}
        for fut in as_completed(futs):
            n = futs[fut]
            try:
                results[n] = fut.result()
            except Exception as exc:
                results[n] = f"{type(exc).__name__}: {exc}"
    return results


def ocr_text_from_digitise(payload: dict) -> str:
    docs = payload.get("documents") or []
    chunks = []
    for doc in docs:
        for page in doc.get("pages") or []:
            blocks = sorted(page.get("blocks") or [],
                            key=lambda b: b.get("reading_order") or 0)
            chunks.append("\n\n".join((b.get("text") or "").strip() for b in blocks if b.get("text")))
    return "\n\n".join(chunks)


def call_sarvam(model: str, messages: list, api_key: str, limiter: RateLimiter,
                timeout: float = 180.0) -> dict:
    limiter.wait()
    r = httpx.post(
        SARVAM_CHAT_URL,
        headers={"api-subscription-key": api_key, "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": 0,
              "max_tokens": 8192,
              "response_format": {"type": "json_object"}},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()


def page_image_message(png_path: Path, text: str) -> list:
    b64 = base64.b64encode(png_path.read_bytes()).decode("ascii")
    return [{
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ],
    }]


def call_sarvam_v2(model: str, messages: list, api_key: str, limiter: "RateLimiter",
                   max_tokens: int = 2048, json_object: bool = True,
                   timeout: float = 180.0) -> dict:
    blob = json.dumps(messages)
    if "image_url" in blob and model not in IMAGE_MODELS:
        raise ValueError(f"{model} must not receive a PNG on this Sarvam key")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    if json_object:
        payload["response_format"] = {"type": "json_object"}
    last_exc = None
    backoff = 2.0
    for _attempt in range(12):
        limiter.wait()
        try:
            r = httpx.post(
                SARVAM_V2_CHAT_URL,
                headers={"api-subscription-key": api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=timeout,
            )
            if r.status_code == 429:
                time.sleep(backoff)
                backoff = min(backoff * 2, 90)
                last_exc = httpx.HTTPStatusError(
                    "429 Too Many Requests", request=r.request, response=r
                )
                continue
            if r.status_code in (502, 503, 504):
                last_exc = httpx.HTTPStatusError(
                    f"{r.status_code} {r.reason_phrase}", request=r.request, response=r
                )
                if _attempt >= 2:
                    r.raise_for_status()
                time.sleep(5)
                continue
            r.raise_for_status()
            return r.json()
        except httpx.TimeoutException as exc:
            last_exc = exc
            time.sleep(backoff)
            backoff = min(backoff * 2, 90)
            continue
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 429:
                last_exc = exc
                time.sleep(backoff)
                backoff = min(backoff * 2, 90)
                continue
            if status in (502, 503, 504) and _attempt < 2:
                last_exc = exc
                time.sleep(5)
                continue
            raise
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("sarvam v2 failed")


def call_gemini(model: str, parts: list, api_key: str, timeout: float = 180.0) -> dict:
    r = httpx.post(
        f"{GEMINI_CHAT_URL}/{model}:generateContent?key={api_key}",
        json={"contents": [{"parts": parts}],
              "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()
