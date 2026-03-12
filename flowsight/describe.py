"""
Description generation module.

For every sample (real or synthetic) this module generates a rich 7-section
plain-text description and saves it as dataset/<id>/description.txt.

Strategy by data_type:
  real        — multimodal call: image + mermaid source + context.json (repo tree, readme,
                doc context, selected file snippets).  Produces the highest-density output.
  meaningful  — multimodal call: image + mermaid source.  No repo context available.
                "Repository Context" section describes diagram-internal terms only.
  chaos       — multimodal call: image + mermaid source.  Sections may state incoherence.
  misleading  — multimodal call: image + mermaid source + introduced_errors injection.
                Annotator is reminded to describe what IS shown — not correct errors.

Resumable: samples with an existing description.txt are skipped by default.
  --overwrite      re-generate everything
  --retry-failed   re-generate only samples listed in describe_progress.json["failed_ids"]

Usage (via main.py):
  python main.py describe [--type real|meaningful|chaos|misleading|all]
                          [--overwrite] [--retry-failed]
"""
from __future__ import annotations

import base64
import re
import time
from pathlib import Path

import env_config
from flowsight.config import (
    DATASET_DIR,
    REAL_METADATA,
    SYNTH_METADATA,
    DESCRIBE_PROGRESS,
    DESCRIBE_LOG,
    MAX_MMD_CHARS,
)
from flowsight.utils import (
    log as _log,
    load_json,
    save_json,
    image_to_data_url,
    openrouter_chat,
    trim,
    load_progress,
    save_progress,
    now_ts,
)

MAX_RETRIES = 4
RETRY_SLEEP = 5

OPENROUTER_VISION_URL = "https://openrouter.ai/api/v1/chat/completions"

import requests


def log(msg: str) -> None:
    _log(msg)


# ── System message ────────────────────────────────────────────────────────────

SYSTEM_MSG = (
    "You are a senior technical annotator producing high-density structured descriptions of "
    "flowchart and architecture diagrams. Follow these five annotation rules strictly:\n"
    "1. Information density must be ≥ the diagram itself; a reader should be able to "
    "reconstruct the diagram from your text alone.\n"
    "2. Respect real-world information present in the diagram; prioritise provided README, "
    "source documentation, repo tree, and selected code files.\n"
    "3. Explain all terms, components, and flows in full; do not invent information beyond "
    "available context.\n"
    "4. This description serves as QA ground truth; it must cover explicit diagram content, "
    "implied structure, and any provided repository context.\n"
    "5. If a node or edge is visible in the diagram but lacks further documentation context, "
    "explicitly state: 'visible in diagram; no further repository context available.'"
)

# ── 7-section format ──────────────────────────────────────────────────────────

BASE_FORMAT = """\
Write the description using exactly these seven sections (Markdown headings as shown).

## Diagram Type & Purpose
2–4 sentences: what type of diagram is this (flowchart / sequence / architecture / state machine …), \
what subject does it depict, and what role does it play in the system or repository.

## Overall Layout
1–3 sentences: primary direction (TD/LR/TB/RL), overall hierarchy, start node(s) and end node(s).

## Subgraphs / Stages
If the diagram contains explicit subgraphs, lanes, stages, or phases, describe each one briefly. \
If none exist, write: "No explicit subgraphs; logically divided into N stages: <list>."

## Node-by-Node Description
List every key node. Format per entry:
- **NodeID / Label**: what this node represents in the diagram.
  If confirmed by README or code context, add: "In the repository this corresponds to …"
  If not: "visible in diagram; no further repository context available."

## Edges, Branches & Convergence
One line per significant edge or decision branch:
  `Source --> Destination`: description of what triggers this transition or data flow.
  `D -- Yes --> E` / `D -- No --> F`: describe the branch condition and both outcomes.
Explicitly state where multiple paths converge.

## Repository Context & Terminology
{context_section_instruction}

## High-Density QA Ground Truth Summary
One dense paragraph (≥ 120 words) covering:
- The start node and immediate first steps.
- Every key branch and its conditions.
- The core intermediate nodes and their sequence.
- The end node(s).
- At least 1–2 anchors connecting diagram elements to repository or domain context.
This summary is the primary reference for question answering and must be self-contained.
"""

CONTEXT_REAL = """\
3–8 items. Explain technical terms, module names, file references, or configurations \
visible in the diagram. Cite selected source files or README passages where applicable. \
Example format:
- **TermOrComponent**: explanation with repository evidence."""

CONTEXT_MEANINGFUL = """\
3–8 items. Explain the technical terms, component names, and domain concepts used in \
diagram node labels and edges. No real repository is available — base explanations on \
standard industry usage for this type of system.\
Example format:
- **TermOrComponent**: standard technical meaning in this domain context."""

CONTEXT_CHAOS = """\
3–8 items. Explain each term and component based on its role and relationships within \
the diagram itself. These terms may not correspond to widely known products or standards; \
describe what the diagram shows about each component's function, inputs, and outputs. \
Focus on structural position and flow behavior.\
"""

CONTEXT_MISLEADING = """\
3–8 items. Explain the technical terms and component names used in this diagram. \
For each term, briefly note its standard real-world meaning, then describe how it is \
actually used in THIS diagram (which may differ from standard practice). \
Your description must reflect what the diagram shows — do not correct or normalise the flow.\
"""

MISLEADING_NOTE = """\

CRITICAL ANNOTATION RULE: This diagram is **intentionally misleading** and contains \
deliberate counterfactual errors. Your description MUST strictly reflect what is shown \
in the diagram — do NOT correct errors, normalise flows, or apply domain common sense. \
The introduced errors are:
{introduced_errors}
Every section must describe the diagram as-is, even where it contradicts standard practice."""


# ── Build prompt ──────────────────────────────────────────────────────────────

def _build_prompt(
    sample_dir: Path,
    data_type: str,
    mmd_text: str,
    meta: dict,
) -> tuple[list[dict], str | None]:
    """
    Return (messages_list, system_message).
    messages_list is a list of OpenAI-format message dicts with vision content where relevant.
    """
    png_path = sample_dir / "diagram.png"
    has_image = png_path.exists()

    if data_type == "real":
        context_instr = CONTEXT_REAL
    elif data_type == "meaningful":
        context_instr = CONTEXT_MEANINGFUL
    elif data_type == "chaos":
        context_instr = CONTEXT_CHAOS
    else:  # misleading
        context_instr = CONTEXT_MISLEADING

    format_block = BASE_FORMAT.replace("{context_section_instruction}", context_instr)

    # Build the text portion of the user prompt
    parts: list[str] = []

    if data_type == "misleading":
        errors = meta.get("introduced_errors", [])
        error_str = "\n".join(f"- {e}" for e in errors) if errors else "- (see diagram)"
        parts.append(MISLEADING_NOTE.format(introduced_errors=error_str))

    parts.append(f"**Mermaid source** (may be truncated):\n```mermaid\n{trim(mmd_text, MAX_MMD_CHARS)}\n```")

    if data_type == "real":
        ctx = load_json(sample_dir / "context.json", default={})
        if ctx.get("readme_text"):
            parts.append(f"**README excerpt**:\n{ctx['readme_text']}")
        if ctx.get("doc_context"):
            parts.append(f"**Source document context**:\n{ctx['doc_context']}")
        if ctx.get("snippets"):
            joined = "\n\n".join(ctx["snippets"][:4])
            parts.append(f"**Selected source file snippets**:\n{joined}")
        repo = ctx.get("repo", "")
        if repo:
            parts.append(f"**Repository**: {repo}")

    parts.append(format_block)

    text_prompt = "\n\n".join(parts)

    if has_image:
        data_url = image_to_data_url(png_path)
        user_content = [
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": text_prompt},
        ]
    else:
        user_content = text_prompt  # type: ignore[assignment]

    messages = [
        {"role": "system", "content": SYSTEM_MSG},
        {"role": "user", "content": user_content},
    ]
    return messages, SYSTEM_MSG


# ── Vision-capable LLM call ───────────────────────────────────────────────────

def _call_vision(messages: list, api_key: str, model: str) -> str | None:
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2_800,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/flowsight-dataset",
        "X-Title": "FlowSight Describe",
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
            log(f"    vision error (attempt {attempt+1}): {e}")
            time.sleep(RETRY_SLEEP * (attempt + 1))
    return None


# ── Sample enumeration ────────────────────────────────────────────────────────

def _iter_samples(describe_type: str) -> list[tuple[Path, str, dict]]:
    """
    Yield (sample_dir, data_type, meta_dict) for all relevant samples.
    Ordering: real 000–499 → meaningful → chaos → misleading.
    """
    results: list[tuple[Path, str, dict]] = []

    if describe_type in ("real", "all"):
        meta_list = load_json(REAL_METADATA, default=[])
        for meta in meta_list:
            sid = f"{int(meta['id']):03d}"
            results.append((DATASET_DIR / sid, "real", meta))

    synth_meta = load_json(SYNTH_METADATA, default=[])
    synth_by_id: dict[str, dict] = {m["id"]: m for m in synth_meta}

    def _collect_synth(pattern: str, data_type: str) -> None:
        dirs = sorted(DATASET_DIR.glob(pattern), key=lambda p: p.name)
        for d in dirs:
            if d.is_dir():
                meta = synth_by_id.get(d.name, {"id": d.name})
                results.append((d, data_type, meta))

    if describe_type in ("meaningful", "all"):
        _collect_synth("meaningful_*", "meaningful")
    if describe_type in ("chaos", "all"):
        _collect_synth("nonsense_chaos_*", "chaos")
    if describe_type in ("misleading", "all"):
        _collect_synth("nonsense_misleading_*", "misleading")
    return results


def _infer_type(meta: dict, sample_dir: Path) -> str:
    """Infer data_type from sample directory name."""
    name = sample_dir.name
    if name.startswith("meaningful_"):
        return "meaningful"
    if name.startswith("nonsense_chaos_"):
        return "chaos"
    if name.startswith("nonsense_misleading_"):
        return "misleading"
    return "real"


# ── Public run interface ──────────────────────────────────────────────────────

def run(
    describe_type: str = "all",
    overwrite: bool = False,
    retry_failed: bool = False,
    workers: int = 5,
) -> None:
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    api_key = env_config.get_openrouter_api_key()
    model = env_config.get_generation_model()
    if not api_key:
        log("ERROR: OPENROUTER_API_KEY not set — aborting describe.")
        return

    progress = load_progress(DESCRIBE_PROGRESS)
    completed: set[str] = set(progress["completed_ids"])
    failed: set[str] = set(progress["failed_ids"])
    progress_lock = threading.Lock()

    def _save_progress_safe() -> None:
        with progress_lock:
            progress["completed_ids"] = list(completed)
            progress["failed_ids"] = list(failed)
            save_progress(DESCRIBE_PROGRESS, progress)

    samples = _iter_samples(describe_type)

    # Filter to only work items
    pending: list[tuple] = []
    skip_count_pre = 0
    for sample_dir, data_type, meta in samples:
        sid = sample_dir.name
        effective_type = _infer_type(meta, sample_dir)
        mmd_path = sample_dir / "diagram.mmd"
        desc_path = sample_dir / "description.txt"
        if not mmd_path.exists():
            skip_count_pre += 1
            continue
        already_done = desc_path.exists() and sid in completed
        if already_done and not overwrite and not (retry_failed and sid in failed):
            skip_count_pre += 1
            continue
        if retry_failed and sid not in failed and not overwrite:
            skip_count_pre += 1
            continue
        pending.append((sample_dir, effective_type, meta))

    effective_workers = min(workers, len(pending)) if pending else 1
    log(f"[describe] type={describe_type} pending={len(pending)} skip={skip_count_pre} "
        f"already_done={len(completed)} workers={effective_workers}")

    ok_count = skip_count = fail_count = 0

    def _process_one(item: tuple) -> tuple[str, "str | None"]:
        """Returns (sid, description_or_None)."""
        sample_dir, effective_type, meta = item
        sid = sample_dir.name
        mmd_path = sample_dir / "diagram.mmd"
        mmd_text = mmd_path.read_text(encoding="utf-8")
        log(f"  [{sid}] type={effective_type} …")
        messages, _ = _build_prompt(sample_dir, effective_type, mmd_text, meta)
        description = _call_vision(messages, api_key, model)
        return sid, description

    with ThreadPoolExecutor(max_workers=effective_workers) as executor:
        future_to_item = {executor.submit(_process_one, item): item for item in pending}
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            sample_dir = item[0]
            sid = sample_dir.name
            desc_path = sample_dir / "description.txt"
            try:
                _, description = future.result()
            except Exception as exc:
                log(f"  [{sid}] thread exception: {exc}")
                description = None

            if not description or len(description) < 80:
                log(f"  [{sid}] FAILED — got: {str(description)[:80]}")
                with progress_lock:
                    failed.add(sid)
                fail_count += 1
                _save_progress_safe()
            else:
                desc_path.write_text(description, encoding="utf-8")
                with progress_lock:
                    completed.add(sid)
                    failed.discard(sid)
                ok_count += 1
                log(f"  [{sid}] OK ({len(description)} chars)")
                _save_progress_safe()

    log(f"\n[describe done] ok={ok_count} skip={skip_count_pre} fail={fail_count}")
