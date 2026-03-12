"""
Benchmark evaluation module.

Evaluates multimodal models on FlowSight QA questions with full parallelism.

State machine:
  Each (model, sample) pair is a task stored in <benchmark_dir>/state.json.
  Statuses: pending → running → done | failed | skipped
  On startup, any "running" tasks are automatically reset to "pending" (crash recovery).

Sub-commands:
  init           Build state.json from current dataset
  run            Execute all pending tasks with ThreadPoolExecutor
  status         Print progress summary
  retry-failed   Reset failed tasks back to pending and run again

Key flags:
  --workers N       parallel threads (default 25)
  --qa-mode batch   send all QA in one API call (default)
  --qa-mode single  send each QA item as a separate API call with its own image
  --allow-partial   skip models that fail probe checks

Usage (via main.py):
  python main.py benchmark init
  python main.py benchmark run --workers 25 --qa-mode batch --allow-partial
  python main.py benchmark status
  python main.py benchmark retry-failed --workers 25
"""
from __future__ import annotations

import json
import os
import random
import re
import signal
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import requests

import env_config
from flowsight.config import (
    DATASET_DIR,
    BENCHMARK_DIR,
    REAL_METADATA,
    SYNTH_METADATA,
    DEFAULT_BENCHMARK_COUNTS,
)
from flowsight.utils import (
    log as _log,
    load_json,
    save_json,
    image_to_data_url,
    now_ts,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
STATE_FILE = "state.json"
SELECTION_FILE = "selection_manifest.json"
PAUSE_FLAG = "PAUSE.flag"
RUN_LOG = "run.log"
PROBE_HISTORY = "probe_history.jsonl"

MAX_RETRIES = 4
RETRY_SLEEP = 6
PROGRESS_EVERY = 20   # print lightweight progress every N completed tasks
REPORT_EVERY = 5      # print full analysis report every N progress checkpoints

_state_lock = threading.Lock()
_stop_flag = threading.Event()


def log(msg: str) -> None:
    _log(msg, BENCHMARK_DIR / RUN_LOG)


# ── Path helpers ──────────────────────────────────────────────────────────────

def _rel_path(sample_id: str) -> str:
    from flowsight.config import PROJECT_ROOT
    try:
        base = str(DATASET_DIR.relative_to(PROJECT_ROOT))
    except ValueError:
        base = str(DATASET_DIR)
    sid = f"{int(sample_id):03d}" if (sample_id.isdigit() or re.match(r"^\d{3}$", sample_id)) else sample_id
    return f"{base}/{sid}"


def _abs_path(rel: str) -> Path:
    from flowsight.config import PROJECT_ROOT
    p = Path(rel)
    if p.is_absolute():
        return DATASET_DIR / p.name
    return PROJECT_ROOT / rel


# ── API helpers ───────────────────────────────────────────────────────────────

def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/flowsight-dataset",
        "X-Title": "FlowSight Benchmark",
    }


def _probe(model: str, api_key: str) -> tuple[bool, str]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with a single uppercase letter A and nothing else."}],
        "max_tokens": 5,
        "temperature": 0.0,
    }
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=_headers(api_key), json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if "error" in data:
                    return False, f"embedded error: {data['error'].get('message','')[:120]}"
                content = data["choices"][0]["message"].get("content")
                if content is None:
                    return False, f"content=null: {str(data)[:200]}"
                return True, content.strip()
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            time.sleep(3)
    return False, "no response after 3 attempts"


def _parse_answers(raw: str, n: int) -> list[str]:
    raw = re.sub(r"```[a-z]*\s*", "", raw).strip().rstrip("`").strip()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x).strip().upper()[:1] for x in data]
    except json.JSONDecodeError:
        pass
    letters = re.findall(r'\b([A-D])\b', raw.upper())
    if len(letters) >= n:
        return letters[:n]
    m = re.findall(r'[A-D]', raw.upper())
    return m[:n] if len(m) >= n else (m + ["A"] * n)[:n]


def _parse_single_answer(raw: str) -> str:
    raw = raw.strip().upper()
    for ch in raw:
        if ch in "ABCD":
            return ch
    return "A"


# ── Model call: batch mode (all QA in one call) ──────────────────────────────

def _build_questions_block(qa: list[dict]) -> str:
    lines = []
    for i, item in enumerate(qa):
        lines.append(f"Q{i+1}. {item['question']}")
        for opt in item["options"]:
            lines.append(f"  {opt}")
    return "\n".join(lines)


def _extract_usage(data: dict) -> dict:
    """Extract token usage from API response into a flat dict."""
    raw = data.get("usage", {})
    details = raw.get("completion_tokens_details") or {}
    return {
        "prompt_tokens": raw.get("prompt_tokens", 0),
        "completion_tokens": raw.get("completion_tokens", 0),
        "total_tokens": raw.get("total_tokens", 0),
        "reasoning_tokens": details.get("reasoning_tokens"),
    }


def _call_model_batch(
    model: str, sample_dir: Path, qa: list[dict], api_key: str,
) -> tuple[list[str] | None, dict]:
    """Returns (answers_or_None, usage_dict)."""
    n = len(qa)
    questions_block = _build_questions_block(qa)
    text_prompt = (
        f"You will see a flowchart/architecture diagram and {n} single-choice questions "
        f"about it. Answer each question.\n\n"
        f"[RULES — strictly follow]\n"
        f"- Your reply MUST be exactly one JSON array of length {n}.\n"
        f'- Each element MUST be a single uppercase letter: "A", "B", "C", or "D".\n'
        f"- Element i (0-based) is the answer to Q{{i+1}}.\n"
        f"- Output NO explanation, punctuation, newlines, code fences, or any other text.\n\n"
        f"Questions:\n{questions_block}\n\n"
        f"Output the JSON array directly:"
    )
    png_path = sample_dir / "diagram.png"
    if png_path.exists():
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
        "max_tokens": 64,
        "temperature": 0.0,
    }
    for attempt in range(MAX_RETRIES):
        if _stop_flag.is_set():
            return None, {}
        try:
            r = requests.post(OPENROUTER_URL, headers=_headers(api_key), json=payload, timeout=120)
            if r.status_code == 200:
                data = r.json()
                if "error" in data:
                    log(f"    [{model}] embedded error: {data['error'].get('message','')[:120]}")
                    time.sleep(RETRY_SLEEP * (attempt + 1))
                    continue
                content = data["choices"][0]["message"].get("content")
                if content is None:
                    log(f"    [{model}] content=null")
                    time.sleep(RETRY_SLEEP * (attempt + 1))
                    continue
                return _parse_answers(content.strip(), n), _extract_usage(data)
            log(f"    [{model}] HTTP {r.status_code}: {r.text[:160]}")
            if r.status_code in (401, 402, 403):
                return None, {}
            time.sleep(RETRY_SLEEP * (attempt + 1))
        except Exception as exc:
            log(f"    [{model}] attempt {attempt+1} exception: {exc}")
            time.sleep(RETRY_SLEEP * (attempt + 1))
    return None, {}


# ── Model call: single mode (one QA per API call) ────────────────────────────

def _call_model_single(
    model: str, sample_dir: Path, qa: list[dict], api_key: str,
) -> tuple[list[str] | None, dict]:
    """Returns (answers_or_None, accumulated_usage_dict)."""
    png_path = sample_dir / "diagram.png"
    has_image = png_path.exists()
    data_url = image_to_data_url(png_path) if has_image else None

    answers: list[str] = []
    acc_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "reasoning_tokens": 0}
    has_any_reasoning = False

    for i, item in enumerate(qa):
        if _stop_flag.is_set():
            return None, acc_usage
        opts_str = "\n".join(item["options"])
        text_prompt = (
            f"You see a flowchart/architecture diagram. Answer this single-choice question.\n\n"
            f"Question: {item['question']}\n{opts_str}\n\n"
            f"[RULES]\n"
            f'- Reply with exactly ONE uppercase letter: "A", "B", "C", or "D".\n'
            f"- No explanation or other text.\n\n"
            f"Your answer:"
        )
        if has_image:
            user_content: object = [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": text_prompt},
            ]
        else:
            user_content = text_prompt

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": user_content}],
            "max_tokens": 16,
            "temperature": 0.0,
        }
        got_answer = False
        for attempt in range(MAX_RETRIES):
            if _stop_flag.is_set():
                return None, acc_usage
            try:
                r = requests.post(OPENROUTER_URL, headers=_headers(api_key), json=payload, timeout=60)
                if r.status_code == 200:
                    data = r.json()
                    if "error" in data:
                        time.sleep(RETRY_SLEEP * (attempt + 1))
                        continue
                    content = data["choices"][0]["message"].get("content")
                    if content:
                        answers.append(_parse_single_answer(content))
                        u = _extract_usage(data)
                        acc_usage["prompt_tokens"] += u.get("prompt_tokens", 0)
                        acc_usage["completion_tokens"] += u.get("completion_tokens", 0)
                        acc_usage["total_tokens"] += u.get("total_tokens", 0)
                        rt = u.get("reasoning_tokens")
                        if rt is not None:
                            acc_usage["reasoning_tokens"] += rt
                            has_any_reasoning = True
                        got_answer = True
                        break
                    time.sleep(RETRY_SLEEP * (attempt + 1))
                    continue
                if r.status_code in (401, 402, 403):
                    return None, acc_usage
                time.sleep(RETRY_SLEEP * (attempt + 1))
            except Exception:
                time.sleep(RETRY_SLEEP * (attempt + 1))
        if not got_answer:
            answers.append("A")  # fallback
    if not has_any_reasoning:
        acc_usage["reasoning_tokens"] = None
    return answers, acc_usage


# ── Selection ─────────────────────────────────────────────────────────────────

def _select_samples(counts: dict[str, int]) -> list[dict]:
    rng = random.Random(42)
    out: list[dict] = []

    real_meta = load_json(REAL_METADATA, default=[])
    valid_real = [
        m for m in real_meta
        if (DATASET_DIR / f"{int(m['id']):03d}" / "qa.json").exists()
    ]
    n_real = min(counts.get("real", DEFAULT_BENCHMARK_COUNTS["real"]), len(valid_real))
    chosen_real = rng.sample(valid_real, n_real)
    for m in chosen_real:
        sid = f"{int(m['id']):03d}"
        out.append({"sample_id": sid, "data_type": "real", "path": _rel_path(sid), "source": "real"})

    synth_meta = load_json(SYNTH_METADATA, default=[])
    for dtype, prefix in [("meaningful", "meaningful_"),
                          ("chaos", "nonsense_chaos_"),
                          ("misleading", "nonsense_misleading_")]:
        n = counts.get(dtype, DEFAULT_BENCHMARK_COUNTS.get(dtype, 75))
        candidates = [
            m for m in synth_meta
            if m["id"].startswith(prefix) and (DATASET_DIR / m["id"] / "qa.json").exists()
        ]
        chosen = rng.sample(candidates, min(n, len(candidates)))
        for m in chosen:
            out.append({"sample_id": m["id"], "data_type": dtype,
                        "path": _rel_path(m["id"]), "source": "synthetic"})
    return out


# ── State file helpers ────────────────────────────────────────────────────────

def _load_state() -> dict:
    data = load_json(BENCHMARK_DIR / STATE_FILE, default={})
    data.setdefault("models", [])
    data.setdefault("samples", {})
    data.setdefault("tasks", {})
    data.setdefault("created_at", "")
    for sid, sinfo in data["samples"].items():
        if Path(sinfo.get("path", "")).is_absolute():
            sinfo["path"] = _rel_path(sid)
    return data


def _save_state(state: dict) -> None:
    with _state_lock:
        state["updated_at"] = now_ts()
        save_json(BENCHMARK_DIR / STATE_FILE, state)


def _task_key(model: str, sample_id: str) -> str:
    return f"{model}::{sample_id}"


# ── Statistics helpers ────────────────────────────────────────────────────────

import math as _math
import statistics as _statistics


def _wilson_ci(c: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = c / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * _math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)) / denom
    return max(center - half, 0.0), min(center + half, 1.0)


def _collect_stats(state: dict) -> dict:
    """Aggregate all raw counts from state into one dict of accumulators."""
    QTS   = ["factual", "reasoning", "negation"]
    DIFFS = ["easy", "medium", "hard"]
    DTYPES = ["real", "meaningful", "chaos", "misleading"]

    by_model: dict[str, dict] = defaultdict(lambda: {
        "done": 0, "pending": 0, "failed": 0, "skipped": 0, "running": 0,
        "correct": 0, "total": 0,
    })
    # [correct, total]
    by_dt:    dict[str, list] = defaultdict(lambda: [0, 0])
    by_qt:    dict[str, list] = defaultdict(lambda: [0, 0])
    by_diff:  dict[str, list] = defaultdict(lambda: [0, 0])
    # 2-D cross tables
    dt_qt:   dict[str, list] = defaultdict(lambda: [0, 0])  # "dtype|qt"
    dt_diff: dict[str, list] = defaultdict(lambda: [0, 0])  # "dtype|diff"
    qt_diff: dict[str, list] = defaultdict(lambda: [0, 0])  # "qt|diff"
    m_dt:    dict[str, list] = defaultdict(lambda: [0, 0])  # "model|dtype"
    m_qt:    dict[str, list] = defaultdict(lambda: [0, 0])  # "model|qt"
    m_diff:  dict[str, list] = defaultdict(lambda: [0, 0])  # "model|diff"
    # timing / tokens
    m_elapsed:    dict[str, list] = defaultdict(list)
    m_comp_tok:   dict[str, list] = defaultdict(list)
    m_reason_tok: dict[str, list] = defaultdict(list)

    for task in state["tasks"].values():
        m = task["model"]
        s = task["status"]
        by_model[m][s] = by_model[m].get(s, 0) + 1
        if s != "done":
            continue
        by_model[m]["correct"] += task.get("correct", 0)
        by_model[m]["total"]   += task.get("total", 0)
        sid   = task["sample_id"]
        dtype = state["samples"].get(sid, {}).get("data_type", "?")
        by_dt[dtype][0] += task.get("correct", 0)
        by_dt[dtype][1] += task.get("total", 0)
        m_elapsed[m].append(float(task.get("elapsed_s", 0.0)))
        u  = task.get("usage") or {}
        ct = u.get("completion_tokens", 0)
        if ct:
            m_comp_tok[m].append(ct)
        rt = u.get("reasoning_tokens")
        if rt is not None and rt > 0:
            m_reason_tok[m].append(rt)
        for pq in task.get("per_question", []):
            c    = 1 if pq.get("is_correct") else 0
            qt   = pq.get("type", "?")
            diff = pq.get("difficulty", "?")
            by_qt[qt][0]   += c;  by_qt[qt][1]   += 1
            by_diff[diff][0] += c; by_diff[diff][1] += 1
            dt_qt[f"{dtype}|{qt}"][0]     += c; dt_qt[f"{dtype}|{qt}"][1]     += 1
            dt_diff[f"{dtype}|{diff}"][0] += c; dt_diff[f"{dtype}|{diff}"][1] += 1
            qt_diff[f"{qt}|{diff}"][0]    += c; qt_diff[f"{qt}|{diff}"][1]    += 1
            m_dt[f"{m}|{dtype}"][0]  += c; m_dt[f"{m}|{dtype}"][1]  += 1
            m_qt[f"{m}|{qt}"][0]     += c; m_qt[f"{m}|{qt}"][1]     += 1
            m_diff[f"{m}|{diff}"][0] += c; m_diff[f"{m}|{diff}"][1] += 1

    return dict(
        by_model=by_model, by_dt=by_dt, by_qt=by_qt, by_diff=by_diff,
        dt_qt=dt_qt, dt_diff=dt_diff, qt_diff=qt_diff,
        m_dt=m_dt, m_qt=m_qt, m_diff=m_diff,
        m_elapsed=m_elapsed, m_comp_tok=m_comp_tok, m_reason_tok=m_reason_tok,
        QTS=QTS, DIFFS=DIFFS, DTYPES=DTYPES,
    )


def _pct(acc: dict, key: str) -> str:
    c, t = acc.get(key, [0, 0])
    return f"{c/t*100:>6.1f}%" if t else "    —  "


def _cross_table(
    rows: list[str], cols: list[str], data: dict,
    row_label: str, col_label_fn=None,
) -> list[str]:
    """Render a 2-D cross-table of accuracies."""
    if col_label_fn is None:
        col_label_fn = lambda x: x
    col_w = 11
    hdr_row = f"  {row_label:<20}" + "".join(f"{col_label_fn(c):>{col_w}}" for c in cols)
    lines = [hdr_row, "-" * (22 + col_w * len(cols))]
    for r in rows:
        row = f"  {r:<20}"
        for c in cols:
            cv, tv = data.get(f"{r}|{c}", [0, 0])
            row += f"{cv/tv*100:>{col_w}.1f}%" if tv else f"{'—':>{col_w}}"
        lines.append(row)
    return lines


def _print_progress(state: dict, header: str, done: int, total: int,
                    fail: int, rate: float) -> None:
    """Lightweight per-checkpoint output: just progress bar + per-model summary."""
    acc = _collect_stats(state)
    by_model = acc["by_model"]
    lines = [header]
    lines.append(f"  Progress: {done}/{total} tasks  |  failed: {fail}  |  {rate:.1f} tasks/min")
    lines.append(f"\n  {'Model':<50} {'done':>5} {'pend':>5} {'fail':>5}   {'acc':>7}")
    lines.append("  " + "-" * 72)
    for model in state["models"]:
        s = by_model[model]
        ac = (s["correct"] / s["total"] * 100) if s["total"] else 0
        lines.append(f"    {model:<48} {s['done']:>5} {s['pending']:>5} {s['failed']:>5}   {ac:>6.1f}%")
    log("\n".join(lines) + "\n")


def _print_report(state: dict, header: str) -> None:
    """Full analysis report with all 2-D cross-tables."""
    acc = _collect_stats(state)
    by_model = acc["by_model"]
    by_dt    = acc["by_dt"]
    by_qt    = acc["by_qt"]
    by_diff  = acc["by_diff"]
    dt_qt    = acc["dt_qt"]
    dt_diff  = acc["dt_diff"]
    qt_diff  = acc["qt_diff"]
    m_dt     = acc["m_dt"]
    m_qt     = acc["m_qt"]
    m_diff   = acc["m_diff"]
    m_elapsed    = acc["m_elapsed"]
    m_comp_tok   = acc["m_comp_tok"]
    m_reason_tok = acc["m_reason_tok"]
    QTS   = acc["QTS"]
    DIFFS = acc["DIFFS"]
    DTYPES = acc["DTYPES"]

    has_pq = any(v[1] > 0 for v in by_qt.values())

    def short(m: str) -> str:
        return m.split("/")[-1][:30]

    SEP = "=" * 90
    sep = "-" * 90

    lines = [f"\n{SEP}", header, SEP]

    # ── A. Model progress ──
    lines += [f"\n[A] Model Progress",
              f"  {'Model':<55} {'done':>5} {'pend':>5} {'fail':>5} {'skip':>5}   {'acc':>7}",
              "  " + sep]
    for model in state["models"]:
        s = by_model[model]
        ac = (s["correct"] / s["total"] * 100) if s["total"] else 0
        lines.append(f"    {model:<53} {s['done']:>5} {s['pending']:>5} {s['failed']:>5} "
                     f"{s['skipped']:>5}   {ac:>6.1f}%")

    # ── B. DataType / QAType / Difficulty marginals ──
    if has_pq:
        lines.append(f"\n[B] Marginal Accuracy")
        lines.append(f"  {'DataType':<20} {'acc':>8}   {'QAType':<14} {'acc':>8}   {'Difficulty':<12} {'acc':>8}")
        lines.append("  " + sep)
        for i in range(max(len(DTYPES), len(QTS), len(DIFFS))):
            def _m(lst, d): return f"{d[lst[i]][0]/d[lst[i]][1]*100:.1f}%" if i < len(lst) and d.get(lst[i],[0,0])[1] else ""
            col1 = f"  {DTYPES[i]:<18}  {_m(DTYPES,by_dt):>8}" if i < len(DTYPES) else " " * 30
            col2 = f"  {QTS[i]:<12}  {_m(QTS,by_qt):>8}" if i < len(QTS) else " " * 26
            col3 = f"  {DIFFS[i]:<10}  {_m(DIFFS,by_diff):>8}" if i < len(DIFFS) else ""
            lines.append(col1 + col2 + col3)

    if not has_pq:
        log("\n".join(lines) + "\n")
        return

    # ── C. 2-D cross-tables ──
    # C1. DataType × QAType
    lines.append(f"\n[C1] DataType × QAType")
    lines += _cross_table(DTYPES, QTS, dt_qt, "DataType \\ QAType")

    # C2. DataType × Difficulty
    lines.append(f"\n[C2] DataType × Difficulty")
    lines += _cross_table(DTYPES, DIFFS, dt_diff, "DataType \\ Difficulty")

    # C3. QAType × Difficulty
    lines.append(f"\n[C3] QAType × Difficulty")
    lines += _cross_table(QTS, DIFFS, qt_diff, "QAType \\ Difficulty")

    # C4. Model × DataType
    lines.append(f"\n[C4] Model × DataType")
    col_w = 13
    hdr = f"  {'Model':<32}" + "".join(f"{d:>{col_w}}" for d in DTYPES) + f"{'OVERALL':>{col_w}}"
    lines += [hdr, "  " + "-" * (34 + col_w * (len(DTYPES) + 1))]
    for model in state["models"]:
        row = f"  {short(model):<32}"
        for dt in DTYPES:
            cv, tv = m_dt.get(f"{model}|{dt}", [0, 0])
            row += f"{cv/tv*100:>{col_w}.1f}%" if tv else f"{'—':>{col_w}}"
        s = by_model[model]
        ac = (s["correct"] / s["total"] * 100) if s["total"] else 0
        row += f"{ac:>{col_w}.1f}%"
        lines.append(row)

    # C5. Model × QAType
    lines.append(f"\n[C5] Model × QAType")
    hdr = f"  {'Model':<32}" + "".join(f"{q:>{col_w}}" for q in QTS) + f"{'OVERALL':>{col_w}}"
    lines += [hdr, "  " + "-" * (34 + col_w * (len(QTS) + 1))]
    for model in state["models"]:
        row = f"  {short(model):<32}"
        for qt in QTS:
            cv, tv = m_qt.get(f"{model}|{qt}", [0, 0])
            row += f"{cv/tv*100:>{col_w}.1f}%" if tv else f"{'—':>{col_w}}"
        s = by_model[model]
        ac = (s["correct"] / s["total"] * 100) if s["total"] else 0
        row += f"{ac:>{col_w}.1f}%"
        lines.append(row)

    # C6. Model × Difficulty
    lines.append(f"\n[C6] Model × Difficulty")
    hdr = f"  {'Model':<32}" + "".join(f"{d:>{col_w}}" for d in DIFFS) + f"{'OVERALL':>{col_w}}"
    lines += [hdr, "  " + "-" * (34 + col_w * (len(DIFFS) + 1))]
    for model in state["models"]:
        row = f"  {short(model):<32}"
        for diff in DIFFS:
            cv, tv = m_diff.get(f"{model}|{diff}", [0, 0])
            row += f"{cv/tv*100:>{col_w}.1f}%" if tv else f"{'—':>{col_w}}"
        s = by_model[model]
        ac = (s["correct"] / s["total"] * 100) if s["total"] else 0
        row += f"{ac:>{col_w}.1f}%"
        lines.append(row)

    # ── D. Instruct vs Thinking (Qwen pairs) ──
    _qwen_pairs = [
        ("8b",   "qwen/qwen3-vl-8b-instruct",       "qwen/qwen3-vl-8b-thinking"),
        ("30b",  "qwen/qwen3-vl-30b-a3b-instruct",  "qwen/qwen3-vl-30b-a3b-thinking"),
        ("235b", "qwen/qwen3-vl-235b-a22b-instruct","qwen/qwen3-vl-235b-a22b-thinking"),
    ]
    active_pairs = [(sz, i, t) for sz, i, t in _qwen_pairs
                    if by_model[i]["total"] and by_model[t]["total"]]
    if active_pairs:
        lines.append(f"\n[D] Instruct vs Thinking (Qwen — overall + per DataType)")
        lines.append(f"  {'Size':<6} {'Inst Acc':>10} {'Think Acc':>11} {'Δ':>8}"
                     f"  {'Inst s':>8} {'Think s':>9} {'×':>5}")
        lines.append("  " + sep)
        for sz, inst, think in active_pairs:
            si = by_model[inst]; st = by_model[think]
            ia = si["correct"] / si["total"] * 100
            ta = st["correct"] / st["total"] * 100
            it = sum(m_elapsed[inst]) / max(len(m_elapsed[inst]), 1)
            tt = sum(m_elapsed[think]) / max(len(m_elapsed[think]), 1)
            ratio = tt / it if it > 0 else 0
            lines.append(f"  {sz:<6} {ia:>9.1f}% {ta:>10.1f}% {ta-ia:>+7.1f}%"
                         f"  {it:>7.1f}s {tt:>8.1f}s {ratio:>4.1f}×")
            for dt in DTYPES:
                ic = m_dt.get(f"{inst}|{dt}", [0, 0])
                tc = m_dt.get(f"{think}|{dt}", [0, 0])
                if not ic[1] or not tc[1]:
                    continue
                ip = ic[0]/ic[1]*100; tp = tc[0]/tc[1]*100
                lines.append(f"         {dt:<14} inst={ip:.1f}%  think={tp:.1f}%  Δ={tp-ip:+.1f}%")

    # ── E. Timing & Token stats ──
    lines.append(f"\n[E] Model Timing & Tokens")
    lines.append(f"  {'Model':<32} {'mean_s':>8} {'p50_s':>7} {'p90_s':>7}"
                 f" {'comp_tok':>9} {'reason_tok':>11}")
    lines.append("  " + "-" * 78)
    for model in state["models"]:
        els = m_elapsed[model]
        if not els:
            continue
        mean_t = sum(els) / len(els)
        p50 = _statistics.median(els)
        p90 = sorted(els)[max(int(0.9 * len(els)) - 1, 0)]
        ct_list = m_comp_tok[model]
        rt_list = m_reason_tok[model]
        avg_ct = f"{sum(ct_list)/len(ct_list):.0f}" if ct_list else "—"
        avg_rt = f"{sum(rt_list)/len(rt_list):.0f}" if rt_list else "—"
        lines.append(f"  {short(model):<32} {mean_t:>8.1f} {p50:>7.1f} {p90:>7.1f}"
                     f" {avg_ct:>9} {avg_rt:>11}")

    # ── F. Wilson 95% CI ──
    lines.append(f"\n[F] Model 95% Wilson CI")
    lines.append(f"  {'Model':<32} {'acc':>7} {'nQ':>6}  CI-lo   CI-hi")
    lines.append("  " + "-" * 65)
    for model in state["models"]:
        s = by_model[model]
        if not s["total"]:
            continue
        lo, hi = _wilson_ci(s["correct"], s["total"])
        lines.append(f"  {short(model):<32} {s['correct']/s['total']*100:>6.1f}% {s['total']:>6}"
                     f"  {lo*100:>5.1f}%  {hi*100:>5.1f}%")

    lines.append(f"\n{SEP}\n")
    log("\n".join(lines))


# ── Sub-commands ──────────────────────────────────────────────────────────────

def cmd_init(counts: dict[str, int] | None = None) -> None:
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    models = env_config.get_benchmark_models()
    final_counts = dict(DEFAULT_BENCHMARK_COUNTS)
    if counts:
        final_counts.update(counts)

    log(f"[benchmark init] models={len(models)} counts={final_counts}")
    samples = _select_samples(final_counts)
    log(f"  selected {len(samples)} samples")

    save_json(BENCHMARK_DIR / SELECTION_FILE, samples)

    state: dict = {
        "models": models,
        "samples": {s["sample_id"]: s for s in samples},
        "tasks": {},
        "created_at": now_ts(),
    }
    for model in models:
        for s in samples:
            key = _task_key(model, s["sample_id"])
            state["tasks"][key] = {
                "model": model,
                "sample_id": s["sample_id"],
                "status": "pending",
                "answers": [],
                "correct": 0,
                "total": 0,
                "error": "",
                "updated_at": "",
            }

    _save_state(state)
    log(f"  created {len(state['tasks'])} tasks → {BENCHMARK_DIR / STATE_FILE}")


def cmd_run(workers: int = 1, qa_mode: str = "batch") -> None:
    api_key = env_config.get_openrouter_api_key()
    if not api_key:
        log("ERROR: OPENROUTER_API_KEY not set — aborting benchmark run.")
        return

    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    state = _load_state()
    if not state["tasks"]:
        log("[benchmark run] No tasks found. Run `benchmark init` first.")
        return

    models: list[str] = state["models"]

    # Crash recovery: reset any "running" tasks back to "pending"
    recovered = 0
    for task in state["tasks"].values():
        if task["status"] == "running":
            task["status"] = "pending"
            task["error"] = "auto-recovered from interrupted running state"
            recovered += 1
    if recovered:
        log(f"[benchmark run] recovered {recovered} interrupted tasks → pending")
        _save_state(state)

    # Probe all models — abort immediately on first failure
    log("[benchmark run] probing models …")
    probe_hist = open(BENCHMARK_DIR / PROBE_HISTORY, "a", encoding="utf-8")
    failed_probes: list[str] = []
    for model in models:
        ok, txt = _probe(model, api_key)
        entry = {"model": model, "ok": ok, "response": txt, "ts": now_ts()}
        probe_hist.write(json.dumps(entry) + "\n")
        probe_hist.flush()
        if ok:
            log(f"  [probe][OK] {model} → {txt!r}")
        else:
            log(f"  [probe][FAIL] {model} → {txt}")
            failed_probes.append(model)
    probe_hist.close()
    if failed_probes:
        log(f"[benchmark run] {len(failed_probes)} model(s) failed probe — aborting.")
        for m in failed_probes:
            log(f"  FAILED: {m}")
        return

    # Signal handling
    _stop_flag.clear()
    original_sigint = signal.getsignal(signal.SIGINT)
    original_sigterm = signal.getsignal(signal.SIGTERM)

    def _handle_signal(sig, frame):
        log(f"\n[benchmark] received signal {sig}, stopping workers …")
        _stop_flag.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    pause_path = BENCHMARK_DIR / PAUSE_FLAG

    # Collect pending tasks, interleave across models for best parallelism
    pending_keys = [
        k for k, t in state["tasks"].items()
        if t["status"] == "pending"
    ]
    # Interleave: round-robin by model so parallel workers hit different models
    by_model_keys: dict[str, list[str]] = defaultdict(list)
    for k in pending_keys:
        by_model_keys[state["tasks"][k]["model"]].append(k)
    interleaved: list[str] = []
    max_per_model = max((len(v) for v in by_model_keys.values()), default=0)
    model_lists = list(by_model_keys.values())
    for i in range(max_per_model):
        for ml in model_lists:
            if i < len(ml):
                interleaved.append(ml[i])
    pending_keys = interleaved

    total_pending = len(pending_keys)
    effective_workers = min(workers, total_pending) if total_pending else 1

    log(f"[benchmark run] {total_pending} pending tasks, {len(models)} models, "
        f"workers={effective_workers}, qa_mode={qa_mode}")

    done_count = 0
    fail_count = 0
    checkpoint_count = 0   # counts how many PROGRESS_EVERY milestones have passed
    t_run_start = time.time()

    def _run_one_task(key: str) -> tuple[str, bool]:
        """Execute one benchmark task. Returns (key, success)."""
        nonlocal done_count, fail_count, checkpoint_count
        if _stop_flag.is_set():
            return key, False
        if pause_path.exists():
            return key, False

        task = state["tasks"][key]
        model = task["model"]
        sample_id = task["sample_id"]
        sample_info = state["samples"].get(sample_id, {})
        sample_dir = _abs_path(sample_info.get("path", _rel_path(sample_id)))
        worker_name = threading.current_thread().name

        qa_path = sample_dir / "qa.json"
        if not qa_path.exists():
            with _state_lock:
                task["status"] = "skipped"
                task["error"] = "qa.json missing"
                task["updated_at"] = now_ts()
            _save_state(state)
            return key, False

        qa = load_json(qa_path, default=[])
        if not qa:
            with _state_lock:
                task["status"] = "skipped"
                task["error"] = "qa.json empty"
                task["updated_at"] = now_ts()
            _save_state(state)
            return key, False

        with _state_lock:
            task["status"] = "running"
            task["updated_at"] = now_ts()
        _save_state(state)

        t0 = time.time()
        log(f"  [{worker_name}] [{model}] [{sample_id}] …")

        if qa_mode == "single":
            answers, usage = _call_model_single(model, sample_dir, qa, api_key)
        else:
            answers, usage = _call_model_batch(model, sample_dir, qa, api_key)

        elapsed = time.time() - t0

        if answers is None:
            with _state_lock:
                task["status"] = "failed"
                task["error"] = "no response after retries"
                task["updated_at"] = now_ts()
                fail_count += 1
            _save_state(state)
            log(f"  [{worker_name}] [{model}] [{sample_id}] FAILED ({elapsed:.1f}s)")
            return key, False
        else:
            per_question = []
            correct = 0
            for i, ans in enumerate(answers):
                if i >= len(qa):
                    break
                q = qa[i]
                is_correct = ord(ans) - ord("A") == q.get("correct_index", -1)
                if is_correct:
                    correct += 1
                per_question.append({
                    "idx": i,
                    "answer": ans,
                    "correct_answer": chr(65 + q.get("correct_index", 0)),
                    "is_correct": is_correct,
                    "type": q.get("type", ""),
                    "difficulty": q.get("difficulty", ""),
                })
            with _state_lock:
                task["status"] = "done"
                task["answers"] = answers
                task["correct"] = correct
                task["total"] = len(qa)
                task["per_question"] = per_question
                task["elapsed_s"] = round(elapsed, 2)
                task["usage"] = usage
                task["updated_at"] = now_ts()
                done_count += 1
            _save_state(state)
            log(f"  [{worker_name}] [{model}] [{sample_id}] OK {correct}/{len(qa)} ({elapsed:.1f}s)")

            # Periodic stats
            if done_count % PROGRESS_EVERY == 0:
                nonlocal checkpoint_count
                checkpoint_count += 1
                elapsed_total = time.time() - t_run_start
                rate = done_count / elapsed_total * 60 if elapsed_total > 0 else 0
                hdr = (f"── checkpoint #{checkpoint_count}: "
                       f"{done_count}/{total_pending} done, "
                       f"{fail_count} failed, {rate:.1f} tasks/min ──")
                if checkpoint_count % REPORT_EVERY == 0:
                    _print_report(state, hdr)
                else:
                    _print_progress(state, hdr, done_count, total_pending, fail_count, rate)
            return key, True

    # Execute with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=effective_workers, thread_name_prefix="bm") as executor:
        future_map = {executor.submit(_run_one_task, key): key for key in pending_keys}
        for future in as_completed(future_map):
            if _stop_flag.is_set():
                break
            try:
                future.result()
            except Exception as exc:
                key = future_map[future]
                log(f"  [ERROR] task {key}: {exc}")

    # Restore signal handlers
    signal.signal(signal.SIGINT, original_sigint)
    signal.signal(signal.SIGTERM, original_sigterm)

    elapsed_total = time.time() - t_run_start
    log(f"\n[benchmark run] done_this_run={done_count}, failed={fail_count}, "
        f"elapsed={elapsed_total:.0f}s")
    _print_report(state, "── FINAL SUMMARY ──")


def cmd_status() -> None:
    state = _load_state()
    if not state["tasks"]:
        print("No benchmark state found. Run `benchmark init` first.")
        return
    _print_report(state, "── current status ──")


def cmd_retry_failed() -> None:
    state = _load_state()
    n = 0
    for task in state["tasks"].values():
        if task["status"] == "failed":
            task["status"] = "pending"
            task["error"] = ""
            task["updated_at"] = now_ts()
            n += 1
    _save_state(state)
    log(f"[benchmark retry-failed] reset {n} tasks to pending")


# ── Public run interface ──────────────────────────────────────────────────────

def run(
    sub: str = "run",
    counts: dict[str, int] | None = None,
    workers: int = 1,
    qa_mode: str = "batch",
) -> None:
    if sub == "init":
        cmd_init(counts)
    elif sub == "run":
        cmd_run(workers=workers, qa_mode=qa_mode)
    elif sub == "status":
        cmd_status()
    elif sub == "retry-failed":
        cmd_retry_failed()
        cmd_run(workers=workers, qa_mode=qa_mode)
    else:
        print(f"Unknown benchmark sub-command: {sub!r}")
        print("Available: init | run | status | retry-failed")
