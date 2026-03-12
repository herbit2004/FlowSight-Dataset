"""
Shared utilities: logging, HTTP, OpenRouter API, mermaid.ink rendering,
image encoding, and text helpers.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import re
import threading
import time
from pathlib import Path
from typing import Any

import requests

from flowsight.config import OPENROUTER_URL, MERMAID_INK

# Global lock for log-file writes (used by multi-threaded callers)
_log_file_lock = threading.Lock()


# ── Logging ──────────────────────────────────────────────────────────────────

def log(msg: str, log_file: Path | None = None) -> None:
    """Print to stdout and optionally append to a log file with a timestamp."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{ts}] {msg}"
    try:
        print(msg, flush=True)
    except Exception:
        pass
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with _log_file_lock:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")


# ── JSON helpers ─────────────────────────────────────────────────────────────

def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")


# ── HTTP ──────────────────────────────────────────────────────────────────────

def http_get(
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    timeout: int = 30,
) -> requests.Response | None:
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code in (403, 429):
                reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 65))
                wait = max(reset - int(time.time()), 5) + 3
                time.sleep(min(wait, 90))
            else:
                return r
        except Exception:
            time.sleep(3 * (attempt + 1))
    return None


# ── OpenRouter ────────────────────────────────────────────────────────────────

def openrouter_chat(
    messages: list[dict],
    api_key: str,
    model: str,
    max_tokens: int = 2_000,
    temperature: float = 0.2,
    _log_file: "Path | None" = None,
) -> str | None:
    """Call OpenRouter with retry; returns the assistant message text or None."""

    def _err(msg: str) -> None:
        print(f"[openrouter] {msg}", flush=True)
        if _log_file is not None:
            try:
                _log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(_log_file, "a", encoding="utf-8") as f:
                    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    f.write(f"[{ts}] [openrouter] {msg}\n")
            except Exception:
                pass

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/flowsight-dataset",
        "X-Title": "FlowSight Dataset Build",
    }
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
            if r.status_code == 200:
                data = r.json()
                # Check for embedded error (OpenRouter returns 200 even for provider errors)
                if "error" in data:
                    err_msg = data["error"].get("message", str(data["error"]))
                    _err(f"model={model} embedded error: {err_msg}")
                    time.sleep(6 * (attempt + 1))
                    continue
                content = data["choices"][0]["message"].get("content")
                if content is None:
                    _err(f"model={model} content=null in response: {str(data)[:200]}")
                    time.sleep(6 * (attempt + 1))
                    continue
                return content.strip()
            # Non-200: log and decide whether to retry
            body = r.text[:300]
            _err(f"model={model} HTTP {r.status_code}: {body}")
            if r.status_code in (401, 402, 403):
                # Auth/payment errors won't fix themselves on retry
                _err("Fatal auth/payment error — aborting retries")
                return None
            time.sleep(6 * (attempt + 1))
        except Exception as exc:
            _err(f"model={model} attempt {attempt+1} exception: {exc}")
            time.sleep(6 * (attempt + 1))
    return None


# ── mermaid.ink PNG rendering ─────────────────────────────────────────────────

def render_png(mermaid_code: str, out_path: Path) -> bool:
    """Render Mermaid source to PNG via mermaid.ink; returns True on success."""
    encoded = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("utf-8")
    url = MERMAID_INK.format(encoded=encoded)
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=45)
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ("image" in ct or len(r.content) > 1_000):
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(r.content)
                return True
            time.sleep(3)
        except Exception:
            time.sleep(4)
    return False


# ── Image / data URL ─────────────────────────────────────────────────────────

def image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


# ── Text helpers ──────────────────────────────────────────────────────────────

def trim(text: str, max_chars: int) -> str:
    text = text.strip()
    return text if len(text) <= max_chars else text[:max_chars] + "\n... [truncated]"


def markdown_without_codeblocks(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "[code block omitted]", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


# ── Progress file helpers ─────────────────────────────────────────────────────

def load_progress(path: Path) -> dict:
    data = load_json(path, default={})
    data.setdefault("completed_ids", [])
    data.setdefault("failed_ids", [])
    data.setdefault("updated_at", "")
    return data


def save_progress(path: Path, progress: dict) -> None:
    progress["updated_at"] = now_ts()
    save_json(path, progress)
