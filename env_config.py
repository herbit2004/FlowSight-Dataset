"""
Load API keys and model settings from the project-root .env file.
All scripts import from here — keys are never hard-coded.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path):  # type: ignore
        pass

_PROJECT_ROOT = Path(__file__).resolve().parent
_ENV_LOADED: bool = False


def load_env() -> None:
    """Load .env / .env.local from project root (does not override shell env vars)."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    for name in (".env", ".env.local"):
        p = _PROJECT_ROOT / name
        if p.exists():
            load_dotenv(p, override=False)
    _ENV_LOADED = True


def get_openrouter_api_key() -> str:
    load_env()
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


def get_github_token() -> str:
    load_env()
    return os.environ.get("GITHUB_TOKEN", "").strip()


def get_generation_model() -> str:
    """Model used for crawl quality-check, description generation, and QA generation."""
    load_env()
    return os.environ.get("GENERATION_MODEL", "google/gemini-2.0-flash-001").strip()


def get_benchmark_models() -> list[str]:
    """Comma-separated benchmark model list from .env, or built-in defaults."""
    load_env()
    raw = os.environ.get("BENCHMARK_MODELS", "").strip()
    if raw:
        return [m.strip() for m in raw.split(",") if m.strip()]
    return [
        "qwen/qwen3-vl-8b-instruct",
        "qwen/qwen3-vl-30b-a3b-instruct",
        "qwen/qwen3-vl-235b-a22b-instruct",
        "qwen/qwen3-vl-8b-thinking",
        "qwen/qwen3-vl-30b-a3b-thinking",
        "qwen/qwen3-vl-235b-a22b-thinking",
        "google/gemini-2.5-flash-lite",
        "google/gemini-2.5-flash",
        "bytedance-seed/seed-2.0-mini",
        "openai/gpt-4o-mini",
    ]
