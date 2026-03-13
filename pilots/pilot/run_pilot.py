#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pilot 流程：前 N 条数据 → 多风格 PNG + QA 生成 → 多模型评测。
- 只读 dataset/ 前 PILOT_SIZE 条，所有输出写入 pilot_data/，不覆盖 dataset。
- 风格：default / dark / forest / neutral（mermaid.ink theme）
- QA：基于 Mermaid + description 生成选择题，测试时只给 PNG。
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import time
from pathlib import Path

import requests

# 使用项目根目录下的 dataset，与 build_dataset 一致
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from env_config import load_env, get_openrouter_api_key

load_env()
OPENROUTER_API_KEY = get_openrouter_api_key()

DATASET_DIR = PROJECT_ROOT / "dataset"
# Use script-relative path so this works when pilot/ is under pilots/pilot
PILOT_DIR = Path(__file__).resolve().parent / "pilot_data"
PILOT_SIZE = 10

MERMAID_INK_BASE = "https://mermaid.ink/img/{encoded}?type=png"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

STYLES = [
    ("default", "默认暖色"),
    ("dark", "深色"),
    ("forest", "绿色系"),
    ("neutral", "黑白中性"),
]

VISION_MODELS = [
    "google/gemini-2.0-flash-001",
    "qwen/qwen3.5-flash-02-23",
    "bytedance-seed/seed-2.0-mini",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]

QA_PER_SAMPLE = 5
LOG_PATH = PILOT_DIR / "pilot.log"
EVAL_JSONL_PATH = PILOT_DIR / "eval_results.jsonl"  # 边跑边追加，最后再汇总
PARSE_FAIL_JSONL_PATH = PILOT_DIR / "parse_fail.jsonl"  # 解析失败时记录原始响应


def log(msg: str) -> None:
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{ts}] {msg}\n"
    try:
        print(msg, flush=True)
    except Exception:
        pass
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


# ── 1. 准备 pilot 样本（只读 dataset，写入 pilot_data）────────────────────────
def ensure_pilot_samples() -> list[Path]:
    """复制前 PILOT_SIZE 条的 mmd + description 到 pilot_data/<id>/，返回样本目录列表。"""
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    sample_dirs = []
    for i in range(PILOT_SIZE):
        src = DATASET_DIR / f"{i:03d}"
        dst = PILOT_DIR / f"{i:03d}"
        if not src.exists():
            log(f"  跳过 {src}（不存在）")
            continue
        dst.mkdir(parents=True, exist_ok=True)
        mmd = src / "diagram.mmd"
        desc = src / "description.txt"
        if mmd.exists():
            (dst / "diagram.mmd").write_text(mmd.read_text(encoding="utf-8"), encoding="utf-8")
        if desc.exists():
            (dst / "description.txt").write_text(desc.read_text(encoding="utf-8"), encoding="utf-8")
        sample_dirs.append(dst)
    return sample_dirs


# ── 2. 多风格 PNG 渲染 ───────────────────────────────────────────────────────
def render_style(mermaid_code: str, style_name: str, extra_params: dict, out_path: Path) -> bool:
    encoded = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("utf-8")
    url = MERMAID_INK_BASE.format(encoded=encoded)
    if style_name != "default":
        url += f"&theme={style_name}"
    for k, v in extra_params.items():
        url += f"&{k}={v}"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=50)
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ("image" in ct or len(r.content) > 500):
                out_path.write_bytes(r.content)
                return True
            time.sleep(2)
        except Exception as e:
            log(f"    render {style_name} 异常: {e}")
            time.sleep(3)
    return False


def generate_style_pngs(sample_dirs: list[Path]) -> None:
    for sample_dir in sample_dirs:
        mmd_path = sample_dir / "diagram.mmd"
        if not mmd_path.exists():
            continue
        code = mmd_path.read_text(encoding="utf-8")
        for style_name, _ in STYLES:
            extra = {"bgColor": "1b1b1f"} if style_name == "dark" else {}
            out = sample_dir / f"diagram_{style_name}.png"
            if render_style(code, style_name, extra, out):
                log(f"  {sample_dir.name} {style_name} OK")
            else:
                log(f"  {sample_dir.name} {style_name} FAIL")
            time.sleep(0.5)


# ── 3. QA 生成（仅用 mmd + description，输出选择题）──────────────────────────
def _openrouter_chat(messages: list, max_tokens: int = 2000, temperature: float = 0.2) -> str | None:
    if not OPENROUTER_API_KEY:
        log("  [QA] OPENROUTER_API_KEY 未设置")
        return None
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=90)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            time.sleep(4)
        except Exception as e:
            log(f"  [OpenRouter] {e}")
            time.sleep(4)
    return None


def generate_qa(sample_dir: Path) -> bool:
    mmd_path = sample_dir / "diagram.mmd"
    desc_path = sample_dir / "description.txt"
    if not mmd_path.exists() or not desc_path.exists():
        return False
    mmd = mmd_path.read_text(encoding="utf-8")
    desc = desc_path.read_text(encoding="utf-8")

    prompt = f"""你正在为一张流程图/架构图生成评测用的选择题。题目必须**仅凭图中信息就能回答**，且答案唯一、明确。要求**有一定难度**，能区分“只看图”与“理解不深”的模型。

要求：
1. 共生成 {QA_PER_SAMPLE} 道题，难度混合：
   - 1～2 道事实题：图中节点/边/分支文字直接可见，但选项要含 1～2 个易混项（图中出现过的其他节点或相近表述）。
   - 2～3 道推理题：需多步推理，例如“从节点 X 到节点 Y 会经过哪几个步骤”“若某条件选 No 则最终到达哪”“哪条路径不经过 Z”。
   - 至少 1 道否定/反选题：如“以下哪个**不是**……”“图中**没有**出现的环节是”等，选项里要有图中确实出现的干扰项。
2. 每道题 4 个选项，用 A、B、C、D 标注，正确选项唯一；干扰项要 plausible，不能一眼排除。
3. 题目和选项均用中文，不依赖描述中超出图本身的信息。
4. 只输出一个 JSON 数组，不要其他说明。格式：
[
  {{"question": "题目文字", "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"], "correct_index": 0}},
  ...
]
correct_index 为正确选项在 options 中的下标（0 起）。

Mermaid 源码（供你理解图结构，测试时不会给模型）：
```mermaid
{mmd}
```

图的文字描述（供出题对照；答案必须能从图中直接或推理得出）：
---
{desc[:8000]}
---
请直接输出上述 JSON 数组。"""

    out = _openrouter_chat([{"role": "user", "content": prompt}], max_tokens=2500, temperature=0.3)
    if not out:
        return False
    for attempt in range(2):
        text = out.strip() if attempt == 0 else _openrouter_chat(
            [{"role": "user", "content": prompt}], max_tokens=2500, temperature=0.4
        )
        if not text and attempt == 1:
            break
        if attempt == 1 and text:
            text = text.strip()
        # 去掉 markdown 代码块
        if "```" in text:
            m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
            if m:
                text = m.group(1).strip()
        # 取第一个 [ ] 或 { } 块
        for start, end in [("[", "]"), ("{", "}")]:
            i = text.find(start)
            if i >= 0:
                j = text.rfind(end)
                if j > i:
                    raw = text[i : j + 1]
                    # 尝试修正常见问题：末尾多余逗号
                    raw = re.sub(r",\s*]", "]", raw)
                    raw = re.sub(r",\s*}", "}", raw)
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        try:
                            raw2 = raw.replace("'", '"')
                            data = json.loads(raw2)
                        except json.JSONDecodeError:
                            continue
                    if start == "{":
                        data = [data]
                    if not isinstance(data, list) or len(data) == 0:
                        continue
                    qa_list = []
                    for item in data:
                        q = item.get("question") or item.get("q")
                        opts = item.get("options") or item.get("options_list") or []
                        idx = item.get("correct_index", item.get("correct", 0))
                        if isinstance(idx, str) and len(idx) == 1:
                            idx = ord(idx.upper()) - ord("A")
                        if q and opts and 0 <= idx < len(opts):
                            qa_list.append({"question": q, "options": list(opts), "correct_index": int(idx)})
                    if qa_list:
                        (sample_dir / "qa.json").write_text(
                            json.dumps(qa_list, ensure_ascii=False, indent=2), encoding="utf-8"
                        )
                        return True
        if attempt == 0:
            time.sleep(2)
    log(f"  [QA] 解析失败 sample={sample_dir.name}")
    return False


def run_qa_generation(sample_dirs: list[Path]) -> None:
    for d in sample_dirs:
        if (d / "qa.json").exists():
            log(f"  已有 qa {d.name}，跳过")
            continue
        if generate_qa(d):
            log(f"  QA {d.name} OK")
        else:
            log(f"  QA {d.name} FAIL")
        time.sleep(1.5)


# ── 4. 多模型评测（只发 PNG + 题目与选项，收集答案并判对错）────────────────────
def image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def _parse_message_to_letter(msg: dict) -> str:
    """从 OpenRouter message 中取出 content/reasoning 并解析出 A/B/C/D，解析不到返回 ''。"""
    raw_content = msg.get("content")
    if isinstance(raw_content, list):
        parts = []
        for item in raw_content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text":
                parts.append(item.get("text", item.get("content", "")) or "")
        text = " ".join(parts)
    else:
        text = raw_content or msg.get("reasoning") or msg.get("refusal") or ""
    if text is None:
        text = ""
    text = str(text).strip().upper()
    pred = ""
    if text:
        first_line = text.split("\n")[0].strip()
        if first_line and first_line[0] in "ABCD":
            pred = first_line[0]
        if not pred and first_line and len(first_line) > 0 and first_line[-1] in "ABCD":
            pred = first_line[-1]
        if not pred:
            m = re.search(r"\b([A-D])\b", text)
            if m:
                pred = m.group(1)
        if not pred:
            for c in "ABCD":
                if c in text:
                    pred = c
                    break
    return pred


def probe_models(sample_dirs: list[Path]) -> list[str]:
    """预检：用一张图+简单指令请求每个模型，只保留能正确返回字母的模型。"""
    if not OPENROUTER_API_KEY:
        log("  [probe] OPENROUTER_API_KEY 未设置，跳过预检")
        return list(VISION_MODELS)
    # 取第一张可用图
    probe_image: Path | None = None
    for d in sample_dirs:
        p = d / "diagram_default.png"
        if p.exists():
            probe_image = p
            break
    if not probe_image:
        log("  [probe] 未找到 diagram_default.png，跳过预检")
        return list(VISION_MODELS)
    data_url = image_to_data_url(probe_image)
    prompt = "请只回复一个大写字母 A。不要任何其他文字。"
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]
    passed = []
    for model in VISION_MODELS:
        try:
            r = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "messages": messages, "max_tokens": 16, "temperature": 0},
                timeout=45,
            )
            if r.status_code != 200:
                log(f"  [probe] {model} HTTP {r.status_code}，跳过")
                continue
            body = r.json()
            msg = body.get("choices", [{}])[0].get("message", {})
            letter = _parse_message_to_letter(msg)
            if letter:
                passed.append(model)
                log(f"  [probe] {model} 通过（返回 {letter}）")
            else:
                raw = msg.get("content") or msg.get("reasoning") or ""
                log(f"  [probe] {model} 未解析到字母，跳过。原始: {str(raw)[:80]!r}")
            time.sleep(0.5)
        except Exception as e:
            log(f"  [probe] {model} 异常: {e}，跳过")
    return passed


def answer_one_question(
    image_path: Path,
    question: str,
    options: list[str],
    model: str,
    correct_letter: str,
    sample_id: str = "",
    style_name: str = "",
    qidx: int = 0,
) -> tuple[str, int]:
    if not OPENROUTER_API_KEY:
        return "", 0
    options_text = "\n".join(options)
    # 格式要求写进 user prompt，不用 system（部分模型对 system 限制会 refusal 导致 content 为空）
    prompt = f"""根据所给流程图/架构图图片，回答下面的单选题。

题目：{question}

选项：
{options_text}

【必须遵守】回复仅能是一个大写字母：A、B、C 或 D 之一。不要任何其他文字、标点或解释。
正确示例：B
错误示例：The answer is B、答案是B、B.

请直接输出一个字母："""

    data_url = image_to_data_url(image_path)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 32,
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        if r.status_code != 200:
            return "", 0
        body = r.json()
        msg = body.get("choices", [{}])[0].get("message", {})
        pred = _parse_message_to_letter(msg)
        is_correct = 1 if pred and pred == correct_letter else 0
        if not pred:
            raw_content = msg.get("content")
            raw_preview = (
                (str(raw_content)[:200] if raw_content is not None else "null")
            )
            log(f"    [parse] {model} 未解析到字母，原始: {raw_preview!r}")
            try:
                fail_rec = {
                    "model": model,
                    "sample": sample_id,
                    "style": style_name,
                    "qidx": qidx,
                    "raw_type": type(raw_content).__name__ if raw_content is not None else "None",
                    "raw_preview": raw_preview,
                }
                PILOT_DIR.mkdir(parents=True, exist_ok=True)
                with open(PARSE_FAIL_JSONL_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(fail_rec, ensure_ascii=False) + "\n")
            except Exception:
                pass
        return pred, is_correct
    except Exception as e:
        log(f"    answer_one_question {model} {e}")
        return "", 0


def run_eval(sample_dirs: list[Path]) -> dict:
    """多模型评测：先预检再测，只测能正确返回字母的模型。"""
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVAL_JSONL_PATH, "w", encoding="utf-8") as _:
        pass
    with open(PARSE_FAIL_JSONL_PATH, "w", encoding="utf-8") as _:
        pass

    log("  预检模型（每模型请求一张图+单字母）...")
    models_to_use = probe_models(sample_dirs)
    if not models_to_use:
        log("  无模型通过预检，跳过评测")
        return {"results": []}
    log(f"  通过预检的模型: {models_to_use}")

    total_planned = 0
    for sample_dir in sample_dirs:
        qa_path = sample_dir / "qa.json"
        if not qa_path.exists():
            continue
        qa_list = json.loads(qa_path.read_text(encoding="utf-8"))
        for style_name, _ in STYLES:
            img = sample_dir / f"diagram_{style_name}.png"
            if img.exists():
                total_planned += len(qa_list) * len(models_to_use)
    log(f"  评测计划: 共 {total_planned} 条 (样本×风格×题目×模型)")

    results = []
    total_done = 0
    with open(EVAL_JSONL_PATH, "w", encoding="utf-8") as jf:
        for sample_dir in sample_dirs:
            qa_path = sample_dir / "qa.json"
            if not qa_path.exists():
                log(f"  跳过 {sample_dir.name}（无 qa.json）")
                continue
            qa_list = json.loads(qa_path.read_text(encoding="utf-8"))
            for style_name, _ in STYLES:
                img = sample_dir / f"diagram_{style_name}.png"
                if not img.exists():
                    continue
                log(f"  [eval] 样本 {sample_dir.name} 风格 {style_name} ...")
                for qidx, qa in enumerate(qa_list):
                    correct_idx = qa.get("correct_index", 0)
                    options = qa.get("options", [])
                    if not options or correct_idx >= len(options):
                        continue
                    opt = options[correct_idx]
                    correct_letter = (opt.strip()[0] if opt.strip() else "A").upper()
                    for model in models_to_use:
                        pred, is_correct = answer_one_question(
                            img,
                            qa["question"],
                            options,
                            model,
                            correct_letter,
                            sample_id=sample_dir.name,
                            style_name=style_name,
                            qidx=qidx,
                        )
                        rec = {
                            "sample": sample_dir.name,
                            "style": style_name,
                            "qidx": qidx,
                            "model": model,
                            "correct_letter": correct_letter,
                            "predicted": pred,
                            "correct": is_correct,
                        }
                        results.append(rec)
                        jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        jf.flush()
                        total_done += 1
                        if total_done % 20 == 0:
                            log(f"    已完成 {total_done}/{total_planned} 条")
                        time.sleep(0.3)
    log(f"  评测完成: {total_done} 条 -> {EVAL_JSONL_PATH.name}")
    return {"results": results}


def aggregate_report(raw: dict) -> str:
    results = raw.get("results", [])
    if not results:
        return "无评测结果。"

    by_model = {}
    by_style = {}
    by_model_style = {}
    for r in results:
        m = r["model"]
        s = r["style"]
        c = r.get("correct", 0)
        by_model[m] = by_model.get(m, []) + [c]
        by_style[s] = by_style.get(s, []) + [c]
        key = (m, s)
        by_model_style[key] = by_model_style.get(key, []) + [c]

    lines = ["=== Pilot 评测汇总 ===\n"]
    lines.append("按模型准确率：")
    for m, vals in sorted(by_model.items(), key=lambda x: -sum(x[1]) / max(len(x[1]), 1)):
        acc = sum(vals) / len(vals) * 100
        lines.append(f"  {m}: {acc:.1f}% ({sum(vals)}/{len(vals)})")
    lines.append("\n按风格准确率：")
    for s, vals in sorted(by_style.items(), key=lambda x: -sum(x[1]) / max(len(x[1]), 1)):
        acc = sum(vals) / len(vals) * 100
        lines.append(f"  {s}: {acc:.1f}% ({sum(vals)}/{len(vals)})")
    lines.append("\n按模型×风格：")
    for (m, s), vals in sorted(by_model_style.items()):
        acc = sum(vals) / len(vals) * 100
        lines.append(f"  {m} | {s}: {acc:.1f}%")
    return "\n".join(lines)


# ── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    import sys
    step = (sys.argv[1:] or ["all"])[0].lower()

    # 本轮覆盖之前的日志与评测结果
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    if LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")
    if step in ("all", "eval"):
        # 不 unlink，避免文件被占用时报错；eval 内用 "w" 覆盖写入
        pass

    log("Pilot 开始（仅前 %d 条，输出至 pilot_data，不修改 dataset）" % PILOT_SIZE)
    sample_dirs = ensure_pilot_samples()
    log("样本目录: %s" % [str(p) for p in sample_dirs])

    if step in ("all", "styles", "style"):
        log("Step 1: 多风格 PNG")
        generate_style_pngs(sample_dirs)

    if step in ("all", "qa"):
        log("Step 2: QA 生成")
        run_qa_generation(sample_dirs)

    if step == "probe":
        log("Step: 仅预检模型（不跑评测）")
        passed = probe_models(sample_dirs)
        (PILOT_DIR / "probe_ok.json").write_text(
            json.dumps({"passed": passed, "failed": [m for m in VISION_MODELS if m not in passed]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        log(f"预检完成: 通过 {len(passed)}/{len(VISION_MODELS)} 个模型")
        if passed:
            log("通过: " + ", ".join(passed))
        if len(passed) < len(VISION_MODELS):
            log("未通过: " + ", ".join(m for m in VISION_MODELS if m not in passed))

    if step in ("all", "eval"):
        log("Step 3: 多模型评测（边跑边写 eval_results.jsonl）")
        raw = run_eval(sample_dirs)
        (PILOT_DIR / "eval_results.json").write_text(
            json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        report = aggregate_report(raw)
        log(report)
        (PILOT_DIR / "report.txt").write_text(report, encoding="utf-8")

    log("Pilot 结束")


if __name__ == "__main__":
    main()
