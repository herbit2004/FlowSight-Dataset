#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pilot V4：复用 pilot_v3 的 40 条样本与 QA，但把评测协议改为“同一张图一次性回答全部题”。

与 v3 的核心区别：
- v3：每道题单独发一次图片（每图 6 题 → 每模型 6 次请求）
- v4：每张图只发一次图片，把该图的全部题一次性发出（每图 6 题 → 每模型 1 次请求）

目的：减少重复发送图片造成的 token 成本；代价是任务形态变化（多题同上下文），可能影响准确率与模型差异。
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from env_config import load_env, get_openrouter_api_key

load_env()
API_KEY = get_openrouter_api_key()

PILOT_V3_OUT = PROJECT_ROOT / "pilots" / "pilot_v3" / "out"
OUT_DIR = PROJECT_ROOT / "pilots" / "pilot_v4" / "out"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

QA_TYPES = ("factual", "reasoning", "negation")
QA_DIFFICULTIES = ("easy", "medium", "hard")
QA_PER_SAMPLE = 6

MODELS = [
    "qwen/qwen3-vl-30b-a3b-instruct",
    "qwen/qwen3-vl-30b-a3b-thinking",
    "qwen/qwen3-vl-8b-instruct",
    "qwen/qwen3-vl-8b-thinking",
    "qwen/qwen3-vl-235b-a22b-instruct",
    "qwen/qwen3-vl-235b-a22b-thinking",
]

DATA_TYPES = ("real", "meaningful", "chaos", "misleading")
LOG_PATH = OUT_DIR.parent / "pilot_v4.log"
MANIFEST_PATH = PILOT_V3_OUT / "manifest.json"
EVAL_JSONL_PATH = OUT_DIR / "eval_results.jsonl"


def log(msg: str) -> None:
    OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{ts}] {msg}\n"
    try:
        print(msg, flush=True)
    except Exception:
        pass
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('utf-8')}"


def _message_text(msg: dict) -> str:
    raw = msg.get("content")
    if isinstance(raw, list):
        text = " ".join(
            item.get("text", item.get("content", "")) or ""
            for item in raw
            if isinstance(item, dict) and item.get("type") == "text"
        )
    else:
        text = raw or msg.get("reasoning") or msg.get("refusal") or ""
    return str(text or "").strip()


def _parse_message_to_letter(msg: dict) -> str:
    text = _message_text(msg).strip().upper()
    if not text:
        return ""
    if len(text) == 1 and text in "ABCD":
        return text
    first = text.split("\n")[0].strip()
    if first and first[0] in "ABCD":
        return first[0]
    m = re.search(r"\b([A-D])\b", text)
    if m:
        return m.group(1)
    for c in "ABCD":
        if c in text:
            return c
    return ""


def _extract_json_block(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    if "```" in t:
        m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", t)
        if m:
            t = m.group(1).strip()
    i = t.find("[")
    j = t.rfind("]")
    if i >= 0 and j > i:
        return t[i : j + 1].strip()
    i = t.find("{")
    j = t.rfind("}")
    if i >= 0 and j > i:
        return t[i : j + 1].strip()
    return ""


def _parse_batch_answers(text: str, expected_n: int) -> list[str]:
    """
    允许两种输出：
    1) ["A","B",...]
    2) [{"qidx":0,"answer":"A"}, ...]  或 {"qidx":0,"answer":"A"} 的列表
    """
    raw = _extract_json_block(text)
    if not raw:
        return []
    raw = re.sub(r",\s*]", "]", raw)
    raw = re.sub(r",\s*}", "}", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        try:
            data = json.loads(raw.replace("'", '"'))
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        return []

    # 形式 1：字符串数组
    if all(isinstance(x, str) for x in data):
        letters = [str(x).strip().upper()[:1] for x in data]
        letters = [c for c in letters if c in "ABCD"]
        return letters if len(letters) == expected_n else []

    # 形式 2：对象数组（按 qidx 排序）
    recs = []
    for it in data:
        if not isinstance(it, dict):
            continue
        qidx = it.get("qidx", it.get("index", it.get("qid")))
        ans = it.get("answer", it.get("pred", it.get("choice")))
        if isinstance(ans, str):
            ans = ans.strip().upper()
        if isinstance(qidx, str) and qidx.isdigit():
            qidx = int(qidx)
        if isinstance(qidx, int) and isinstance(ans, str) and ans[:1] in "ABCD":
            recs.append((qidx, ans[:1]))
    if not recs:
        return []
    recs.sort(key=lambda x: x[0])
    letters = [a for _, a in recs]
    return letters if len(letters) == expected_n else []


def probe_models(sample_dirs: list[Path]) -> list[str]:
    if not API_KEY:
        log("  [probe] 未设置 OPENROUTER_API_KEY")
        return list(MODELS)
    img = None
    for d in sample_dirs:
        p = d / "diagram.png"
        if p.exists():
            img = p
            break
    if not img:
        return list(MODELS)
    data_url = image_to_data_url(img)
    prompt = "请只回复一个大写字母 A。不要任何其他文字。"
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": data_url}}]}]
    passed = []
    for model in MODELS:
        try:
            r = requests.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "max_tokens": 16, "temperature": 0},
                timeout=50,
            )
            if r.status_code != 200:
                continue
            msg = r.json().get("choices", [{}])[0].get("message", {})
            letter = _parse_message_to_letter(msg)
            if letter:
                passed.append(model)
            time.sleep(0.5)
        except Exception:
            pass
    return passed


def _answer_batch(image_path: Path, qa_list: list[dict], model: str) -> list[str]:
    if not API_KEY:
        return []
    # 构造一个尽量“硬约束”的输出格式，降低多题时乱输出概率
    blocks = []
    for qidx, qa in enumerate(qa_list):
        opts = qa.get("options", [])
        opt_text = "\n".join(opts)
        blocks.append(f"Q{qidx}. {qa.get('question','')}\n{opt_text}")
    questions_block = "\n\n".join(blocks)
    expected_n = len(qa_list)
    prompt = f"""你将看到一张流程图/架构图，以及该图对应的 {expected_n} 道单选题。请逐题作答。\n\n【必须遵守】\n- 你的回复必须且只能是一个 JSON 数组，长度必须等于 {expected_n}。\n- 数组中的每个元素必须是一个大写字母字符串：\"A\"、\"B\"、\"C\" 或 \"D\"。\n- 第 i 个元素对应 Q{{i}} 的答案。\n- 禁止输出任何解释、标点、换行、代码块或其它文字。\n\n题目如下：\n{questions_block}\n\n请直接输出 JSON 数组："""
    data_url = image_to_data_url(image_path)
    payload_base = {
        "model": model,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": data_url}}]}],
        "max_tokens": 256,
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload_base, timeout=120)
            if r.status_code != 200:
                if attempt < 2:
                    time.sleep(2)
                continue
            msg = r.json().get("choices", [{}])[0].get("message", {})
            text = _message_text(msg)
            answers = _parse_batch_answers(text, expected_n=expected_n)
            if answers:
                return answers
            if attempt < 2:
                time.sleep(2)
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                log(f"    [batch] {model} 异常: {e}")
    return []


def _load_manifest_and_dirs() -> tuple[list[Path], list[dict]]:
    if not MANIFEST_PATH.exists():
        return [], []
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    sample_dirs = []
    for m in manifest:
        dname = m.get("dir", "")
        if not dname:
            continue
        d = PILOT_V3_OUT / dname
        if d.is_dir():
            sample_dirs.append(d)
    return sample_dirs, manifest


def run_eval_batch(sample_dirs: list[Path], manifest: list[dict]) -> dict:
    dir_to_type = {m["dir"]: m["data_type"] for m in manifest}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVAL_JSONL_PATH, "w", encoding="utf-8") as _:
        pass

    log("  预检模型...")
    models_to_use = probe_models(sample_dirs)
    if not models_to_use:
        log("  无模型通过预检")
        return {"results": [], "manifest": manifest}
    log(f"  通过: {len(models_to_use)} 个模型")

    results = []
    done = 0
    max_workers = min(6, len(models_to_use))
    with open(EVAL_JSONL_PATH, "w", encoding="utf-8") as jf:
        for sample_dir in sample_dirs:
            qa_path = sample_dir / "qa.json"
            img_path = sample_dir / "diagram.png"
            if not qa_path.exists() or not img_path.exists():
                continue
            data_type = dir_to_type.get(sample_dir.name, "unknown")
            qa_list = json.loads(qa_path.read_text(encoding="utf-8"))
            if not isinstance(qa_list, list) or not qa_list:
                continue
            # 固定只取前 QA_PER_SAMPLE 条，避免未来改动导致多题超长
            qa_list = qa_list[:QA_PER_SAMPLE]

            correct_letters = []
            for qa in qa_list:
                opts = qa.get("options", [])
                ci = int(qa.get("correct_index", 0) or 0)
                if not opts or ci < 0 or ci >= len(opts) or not str(opts[ci]).strip():
                    correct_letters.append("A")
                else:
                    correct_letters.append(str(opts[ci]).strip()[0].upper())

            def task(m: str):
                return m, _answer_batch(img_path, qa_list, m)

            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {ex.submit(task, m): m for m in models_to_use}
                for fut in as_completed(futures):
                    model, answers = fut.result()
                    ok = bool(answers) and len(answers) == len(qa_list)
                    for qidx, qa in enumerate(qa_list):
                        pred = answers[qidx] if ok else ""
                        correct_letter = correct_letters[qidx]
                        rec = {
                            "sample": sample_dir.name,
                            "data_type": data_type,
                            "qidx": qidx,
                            "type": qa.get("type", "factual"),
                            "difficulty": qa.get("difficulty", "medium"),
                            "model": model,
                            "correct_letter": correct_letter,
                            "predicted": pred,
                            "correct": 1 if pred == correct_letter else 0,
                            "protocol": "batch_per_image",
                        }
                        results.append(rec)
                        jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        jf.flush()
                        done += 1
            time.sleep(0.2)
    log(f"  评测完成: {done} 条")
    return {"results": results, "manifest": manifest}


def aggregate_report(raw: dict) -> str:
    results = raw.get("results", [])
    manifest = raw.get("manifest", [])
    _ = manifest
    if not results:
        return "无结果。"

    def acc(vals):
        return sum(vals) / len(vals) * 100 if vals else 0

    by_model = {}
    by_data_type = {}
    by_model_type = {}
    by_model_data = {}
    for r in results:
        m = r["model"]
        dt = r.get("data_type", "unknown")
        c = r.get("correct", 0)
        by_model.setdefault(m, []).append(c)
        by_data_type.setdefault(dt, []).append(c)
        by_model_type.setdefault((m, r.get("type", "factual")), []).append(c)
        by_model_data.setdefault((m, dt), []).append(c)

    lines = ["=== Pilot V4 汇总（batch-per-image 协议）===\n"]
    lines.append("按数据来源类型：")
    for dt in DATA_TYPES:
        if dt in by_data_type:
            vals = by_data_type[dt]
            lines.append(f"  {dt}: {acc(vals):.1f}% ({sum(vals)}/{len(vals)})")
    lines.append("\n按模型：")
    for m, vals in sorted(by_model.items(), key=lambda x: -acc(x[1])):
        lines.append(f"  {m}: {acc(vals):.1f}% ({sum(vals)}/{len(vals)})")
    lines.append("\n按模型 × 数据来源（核心表）：")
    for (m, dt), vals in sorted(by_model_data.items(), key=lambda x: (x[0][0], x[0][1])):
        lines.append(f"  {m} | {dt}: {acc(vals):.1f}% ({sum(vals)}/{len(vals)})")
    lines.append("\n按模型 × 题目类型：")
    for (m, t), vals in sorted(by_model_type.items()):
        lines.append(f"  {m} | {t}: {acc(vals):.1f}%")
    return "\n".join(lines)


def main() -> None:
    import sys

    step = (sys.argv[1:] or ["eval"])[0].lower()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if step in ("all", "eval") and LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")

    log("Pilot V4 开始（复用 pilot_v3/out 的 40 条样本）")
    sample_dirs, manifest = _load_manifest_and_dirs()
    log(f"样本数: {len(sample_dirs)}（manifest: {MANIFEST_PATH.name}）")

    if step in ("all", "eval"):
        raw = run_eval_batch(sample_dirs, manifest)
        (OUT_DIR / "eval_results.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        report = aggregate_report(raw)
        log(report)
        (OUT_DIR / "report.txt").write_text(report, encoding="utf-8")

    log("Pilot V4 结束")


if __name__ == "__main__":
    main()

