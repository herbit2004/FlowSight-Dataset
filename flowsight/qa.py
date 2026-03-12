"""
QA generation module.

For every sample with a diagram.mmd and description.txt this module generates
a JSON array of multiple-choice questions and saves it as dataset/<id>/qa.json.

Question design principles (fully equivalent to original Chinese version):
  - 6 questions per sample (configurable via QA_PER_SAMPLE in config.py)
  - Distribution: ≥2 reasoning, ≥1 negation; ≤1 easy, ≥2 medium, ≥2 hard
  - Multi-hop, confusable-option, long-chain, and negation question types
  - Distractors are domain-plausible and non-trivially confusable
  - 4 options per question, single correct answer

Output format per question:
  {
    "question": "...",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_index": 0,          // 0-based index into options
    "type": "factual|reasoning|negation",
    "difficulty": "easy|medium|hard"
  }

Resumable: samples with an existing qa.json are skipped by default.
  --overwrite      re-generate all
  --retry-failed   re-generate only failed samples

Usage (via main.py):
  python main.py qa [--type real|meaningful|chaos|misleading|all]
                    [--overwrite] [--retry-failed]
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

import env_config
from flowsight.config import (
    DATASET_DIR,
    REAL_METADATA,
    SYNTH_METADATA,
    QA_PROGRESS,
    QA_LOG,
    MAX_MMD_CHARS,
    QA_PER_SAMPLE,
)
from flowsight.utils import (
    log as _log,
    load_json,
    save_json,
    image_to_data_url,
    trim,
    load_progress,
    save_progress,
    now_ts,
)

MAX_RETRIES = 4
RETRY_SLEEP = 5
OPENROUTER_VISION_URL = "https://openrouter.ai/api/v1/chat/completions"


def log(msg: str) -> None:
    _log(msg)


# ── Prompt ───────────────────────────────────────────────────────────────────

def _build_qa_prompt(mmd_text: str, description: str, data_type: str = "real") -> str:
    # One universal principle + minimal per-type nudge (single variable principle)
    universal_note = (
        "\n**Important**: every correct answer must be derivable solely from the diagram. "
        "Do not assume any prior domain knowledge; treat the diagram as the single source of truth."
    )
    if data_type == "misleading":
        universal_note += (
            " If the diagram's flow differs from common real-world expectations, "
            "the correct answer is still what the diagram shows."
        )

    return (
        f"Generate exactly {QA_PER_SAMPLE} multiple-choice questions about the diagram below.\n"
        f"{universal_note}\n\n"
        f"Each question has a **type** and a **difficulty**. Follow these definitions precisely:\n\n"
        f"### Question types\n"
        f"**factual** — A direct look-up question about a single fact visible in the diagram.\n"
        f"  Examples: 'What is the label of the first node?', 'Which node directly follows X?', "
        f"'How many outgoing edges does node Y have?'\n"
        f"  The answer should be obtainable by finding one specific node or edge — no chaining.\n\n"
        f"**reasoning** — A multi-hop inference question requiring the reader to trace paths, "
        f"combine conditions, or follow sequences across MULTIPLE nodes/edges.\n"
        f"  The longer the reasoning chain, the better. Aim for ≥3 hops for medium, ≥4 hops "
        f"for hard. Examples:\n"
        f"  - 'Starting from A, if condition C1 is Yes and then C2 is No, which node is "
        f"ultimately reached?'\n"
        f"  - 'What is the complete ordered sequence of nodes from X to Y?'\n"
        f"  - 'After A but before reaching Z, which intermediate nodes must be traversed "
        f"and in what order?'\n"
        f"  Distractors must be plausible partial paths or paths with one swap.\n\n"
        f"**negation** — A question phrased with NOT/NEVER/EXCEPT, requiring the reader to "
        f"understand the macro structure and rule out candidates.\n"
        f"  Examples: 'Which of the following is NOT a valid path segment?', "
        f"'Which node does NOT directly connect to any decision diamond?', "
        f"'Which step is NEVER reached if condition X is No?'\n"
        f"  Distractors must include items that ARE present (so 3 options are true, 1 is false).\n\n"
        f"### Difficulty levels — MUST be clearly distinguishable\n"
        f"**easy** — Answerable at a glance with minimal effort. For factual: a single obvious "
        f"node/edge look-up. For reasoning: at most 2 hops. For negation: the NOT-item is "
        f"obviously absent.\n\n"
        f"**medium** — Requires moderate attention. For factual: must scan several nodes to "
        f"confirm. For reasoning: 3 hops, one branch condition. For negation: must check 3–4 "
        f"candidates against the diagram.\n\n"
        f"**hard** — Requires careful analysis. For factual: involves counting, comparing, or "
        f"a subtle detail. For reasoning: ≥4 hops, multiple branch conditions, or comparing two "
        f"parallel paths. For negation: all 4 options look plausible; one requires careful "
        f"structural verification to exclude.\n\n"
        f"### Distribution\n"
        f"- At least 2 **reasoning**, at least 1 **negation**, at least 1 **factual**.\n"
        f"- Difficulty: exactly 1 easy, 2–3 medium, 2–3 hard. "
        f"The easy question should be genuinely trivial; the hard questions should be genuinely "
        f"challenging — a small model should struggle.\n\n"
        f"### Output format\n"
        f"A JSON array (no code fence, no other text). Each element:\n"
        f'{{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], '
        f'"correct_index": 0, "type": "factual|reasoning|negation", '
        f'"difficulty": "easy|medium|hard"}}\n\n'
        f"4 options per question. Single correct answer. Distractors must be domain-plausible "
        f"and non-trivially confusable.\n\n"
        f"Mermaid source:\n```mermaid\n{trim(mmd_text, MAX_MMD_CHARS)}\n```\n\n"
        f"Diagram description (reference only; answers must be derivable from diagram alone):\n"
        f"---\n{description[:7_500]}\n---\n"
        f"Output JSON array:"
    )


# ── Vision-capable LLM call ───────────────────────────────────────────────────

def _call_with_image(
    mmd_text: str,
    description: str,
    png_path: Path,
    api_key: str,
    model: str,
    data_type: str = "real",
) -> str | None:
    text_prompt = _build_qa_prompt(mmd_text, description, data_type=data_type)
    has_image = png_path.exists()
    if has_image:
        data_url = image_to_data_url(png_path)
        user_content: object = [
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": text_prompt},
        ]
    else:
        user_content = text_prompt

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_content}],
        "max_tokens": 3_500,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/flowsight-dataset",
        "X-Title": "FlowSight QA Build",
    }
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(OPENROUTER_VISION_URL, headers=headers, json=payload, timeout=180)
            if r.status_code == 200:
                data = r.json()
                if "error" in data:
                    log(f"    embedded error: {data['error'].get('message', str(data['error']))[:160]}")
                    time.sleep(RETRY_SLEEP * (attempt + 1))
                    continue
                content = data["choices"][0]["message"].get("content")
                if content is None:
                    log(f"    content=null: {str(data)[:200]}")
                    time.sleep(RETRY_SLEEP * (attempt + 1))
                    continue
                return content.strip()
            log(f"    HTTP {r.status_code}: {r.text[:200]}")
            if r.status_code in (401, 402, 403):
                log("    Fatal auth/payment error — aborting retries")
                return None
            time.sleep(RETRY_SLEEP * (attempt + 1))
        except Exception as e:
            log(f"    qa call error (attempt {attempt+1}): {e}")
            time.sleep(RETRY_SLEEP * (attempt + 1))
    return None


# ── Parse and validate JSON ────────────────────────────────────────────────────

def _parse_qa(raw: str) -> list[dict] | None:
    """Robustly extract a JSON array from raw LLM output."""
    # Strip any code fence wrappers first
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip()

    # Strategy 1: direct parse
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # Strategy 2: find the opening '[' and use raw_decode (handles trailing text)
    start = raw.find("[")
    if start >= 0:
        decoder = json.JSONDecoder()
        try:
            data, _ = decoder.raw_decode(raw[start:])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    # Strategy 3: greedy bracket scan (last resort)
    for i, ch in enumerate(raw):
        if ch == "[":
            try:
                data = json.loads(raw[i:])
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass

    return None


def _normalise_options(q: dict) -> dict:
    """
    Ensure each option starts with 'A. '/'B. '/'C. '/'D. '.
    Accepts lists of 4 or 5 items and trims to 4.
    """
    opts = q.get("options", [])
    labels = ["A", "B", "C", "D"]
    normalised = []
    for idx, opt in enumerate(opts[:4]):
        label = labels[idx]
        opt_str = str(opt).strip()
        if not re.match(r"^[A-D][.)]\s", opt_str):
            opt_str = f"{label}. {opt_str}"
        normalised.append(opt_str)
    q["options"] = normalised
    return q


def _validate_qa(qa: list[dict]) -> tuple[bool, str]:
    if len(qa) < QA_PER_SAMPLE:
        return False, f"only {len(qa)} questions (need {QA_PER_SAMPLE})"
    for i, q in enumerate(qa):
        if "question" not in q or "options" not in q or "correct_index" not in q:
            return False, f"item {i} missing required keys"
        if not isinstance(q["options"], list) or len(q["options"]) < 4:
            return False, f"item {i} has fewer than 4 options ({len(q['options'])})"
        # Trim to exactly 4 options (model sometimes gives 5)
        q["options"] = q["options"][:4]
        if not isinstance(q["correct_index"], int) or not (0 <= q["correct_index"] <= 3):
            return False, f"item {i} correct_index out of range ({q['correct_index']})"
    return True, ""


# ── Sample enumeration ────────────────────────────────────────────────────────

def _iter_samples(qa_type: str) -> list[tuple[Path, str]]:
    results: list[tuple[Path, str]] = []

    if qa_type in ("real", "all"):
        meta_list = load_json(REAL_METADATA, default=[])
        for meta in meta_list:
            sid = f"{int(meta['id']):03d}"
            results.append((DATASET_DIR / sid, "real"))

    synth_meta = load_json(SYNTH_METADATA, default=[])
    synth_by_id: dict[str, dict] = {m["id"]: m for m in synth_meta}

    def _collect(pattern: str, dtype: str) -> None:
        for d in sorted(DATASET_DIR.glob(pattern), key=lambda p: p.name):
            if d.is_dir():
                results.append((d, dtype))

    if qa_type in ("meaningful", "all"):
        _collect("meaningful_*", "meaningful")
    if qa_type in ("chaos", "all"):
        _collect("nonsense_chaos_*", "chaos")
    if qa_type in ("misleading", "all"):
        _collect("nonsense_misleading_*", "misleading")

    return results


# ── Public run interface ──────────────────────────────────────────────────────

def run(
    qa_type: str = "all",
    overwrite: bool = False,
    retry_failed: bool = False,
    workers: int = 5,
) -> None:
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    api_key = env_config.get_openrouter_api_key()
    model = env_config.get_generation_model()
    if not api_key:
        log("ERROR: OPENROUTER_API_KEY not set — aborting qa.")
        return

    progress = load_progress(QA_PROGRESS)
    completed: set[str] = set(progress["completed_ids"])
    failed: set[str] = set(progress["failed_ids"])
    progress_lock = threading.Lock()

    def _save_safe() -> None:
        with progress_lock:
            progress["completed_ids"] = list(completed)
            progress["failed_ids"] = list(failed)
            save_progress(QA_PROGRESS, progress)

    samples = _iter_samples(qa_type)

    # Filter to work items
    pending: list[tuple[Path, str]] = []
    skip_count_pre = 0
    for sample_dir, dtype in samples:
        sid = sample_dir.name
        mmd_path = sample_dir / "diagram.mmd"
        desc_path = sample_dir / "description.txt"
        qa_path = sample_dir / "qa.json"
        if not mmd_path.exists() or not desc_path.exists():
            skip_count_pre += 1
            continue
        already_done = qa_path.exists() and sid in completed
        if already_done and not overwrite and not (retry_failed and sid in failed):
            skip_count_pre += 1
            continue
        if retry_failed and sid not in failed and not overwrite:
            skip_count_pre += 1
            continue
        pending.append((sample_dir, dtype))

    effective_workers = min(workers, len(pending)) if pending else 1
    log(f"[qa] type={qa_type} pending={len(pending)} skip={skip_count_pre} "
        f"already_done={len(completed)} workers={effective_workers}")

    ok_count = fail_count = 0

    def _process_one(sample_dir: Path, dtype: str) -> tuple[str, "list | None", str]:
        """Returns (sid, qa_list_or_None, fail_reason)."""
        sid = sample_dir.name
        mmd_text = (sample_dir / "diagram.mmd").read_text(encoding="utf-8")
        description = (sample_dir / "description.txt").read_text(encoding="utf-8")
        png_path = sample_dir / "diagram.png"
        log(f"  [{sid}] type={dtype} …")
        raw = _call_with_image(mmd_text, description, png_path, api_key, model, data_type=dtype)
        if not raw:
            return sid, None, "no response"
        qa_list = _parse_qa(raw)
        if qa_list is None:
            return sid, None, f"JSON parse error: {raw[:80]}"
        ok, reason = _validate_qa(qa_list)
        if not ok:
            return sid, None, f"validation: {reason}"
        return sid, qa_list, ""

    with ThreadPoolExecutor(max_workers=effective_workers) as executor:
        future_map = {
            executor.submit(_process_one, sd, dt): sd
            for sd, dt in pending
        }
        for future in as_completed(future_map):
            sample_dir = future_map[future]
            try:
                sid, qa_list, reason = future.result()
            except Exception as exc:
                sid = sample_dir.name
                qa_list, reason = None, str(exc)

            if qa_list is None:
                log(f"  [{sid}] FAILED — {reason}")
                with progress_lock:
                    failed.add(sid)
                fail_count += 1
                _save_safe()
            else:
                save_json(sample_dir / "qa.json", qa_list)
                with progress_lock:
                    completed.add(sid)
                    failed.discard(sid)
                ok_count += 1
                log(f"  [{sid}] OK ({len(qa_list)} questions)")
                _save_safe()

    log(f"\n[qa done] ok={ok_count} skip={skip_count_pre} fail={fail_count}")
