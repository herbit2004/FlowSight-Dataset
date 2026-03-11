#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一从环境配置文件加载 API Key，避免硬编码。
优先读取项目根目录下的 .env 文件（该文件已加入 .gitignore，请勿提交）。
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
    """从项目根目录的 .env 加载环境变量（可被环境变量覆盖）。"""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    for name in (".env", ".env.local"):
        p = _PROJECT_ROOT / name
        if p.exists():
            load_dotenv(p, override=False)
    _ENV_LOADED = True


def get_openrouter_api_key() -> str:
    """OpenRouter API Key，用于调用多模型接口。"""
    load_env()
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


def get_github_token() -> str:
    """GitHub Token，用于提高 API 限额（可选）。"""
    load_env()
    return os.environ.get("GITHUB_TOKEN", "").strip()
