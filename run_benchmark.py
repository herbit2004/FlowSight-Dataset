#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlowSight 全量评测脚本（可断点续跑版）

目标：
1) 随机抽样 500 条（默认分层：real 250 / meaningful 100 / chaos 75 / misleading 75）
2) 每次请求“1 张图 + 该图全部 QA 一次性作答”
3) 单线程串行（任务顺序随机）
4) 支持预检、暂停、恢复、补全、失败重试
5) 阶段性输出进度与统计

典型用法：
  python run_benchmark.py init
  python run_benchmark.py run
  python run_benchmark.py status
  python run_benchmark.py pause
  python run_benchmark.py resume
  python run_benchmark.py retry_failed

说明：
- 每次 run 前都会先做模型预检（默认严格：任一模型失败则不启动正式评测）
- 若网络中断/手动 Ctrl+C，下次直接 run 可从 state 继续
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import random
import re
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_DIR = PROJECT_ROOT / "dataset"
REAL_METADATA = DATASET_DIR / "metadata.json"
SYNTH_METADATA = DATASET_DIR / "synthetic_metadata.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_OUT_DIR = PROJECT_ROOT / "benchmark_run"
DEFAULT_SEED = 42

DEFAULT_COUNTS = {
    "real": 250,
    "meaningful": 100,
    "chaos": 75,
    "misleading": 75,
}

MODELS = [
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

PAUSE_FILE = "PAUSE.flag"
STATE_FILE = "state.json"
RESULTS_JSONL = "results.jsonl"
RESPONSES_JSONL = "responses.jsonl"
LOG_FILE = "run.log"
PROBE_HISTORY = "probe_history.jsonl"
SELECTION_FILE = "selection_manifest.json"


class GracefulStop(Exception):
    pass


STOP_REQUESTED = False


def _on_signal(_sig, _frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True


signal.signal(signal.SIGINT, _on_signal)
signal.signal(signal.SIGTERM, _on_signal)


@dataclass
class SampleItem:
    sample_id: str
    data_type: str
    path: str
    source: str
    nonsense_subtype: str = ""


def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, obj: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def log(out_dir: Path, msg: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    line = f"[{now_ts()}] {msg}"
    print(msg, flush=True)
    with open(out_dir / LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_api_key() -> str:
    from env_config import get_openrouter_api_key
    return get_openrouter_api_key()


def image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def message_text(msg: dict) -> str:
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


def extract_json_block(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    if "```" in t:
        m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", t)
        if m:
            t = m.group(1).strip()
    i, j = t.find("["), t.rfind("]")
    if i >= 0 and j > i:
        return t[i : j + 1].strip()
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        return t[i : j + 1].strip()
    return ""


def parse_batch_answers(text: str, expected_n: int) -> list[str]:
    raw = extract_json_block(text)
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

    if all(isinstance(x, str) for x in data):
        letters = [str(x).strip().upper()[:1] for x in data]
        letters = [c for c in letters if c in "ABCD"]
        return letters if len(letters) == expected_n else []

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


def ensure_required_files(sample_dir: Path) -> bool:
    return (sample_dir / "diagram.png").exists() and (sample_dir / "qa.json").exists()


def sample_dir_path(sample_id: str) -> str:
    """样本目录相对 PROJECT_ROOT 的路径，用于持久化，避免绝对路径."""
    return f"dataset/{sample_id}"


def resolve_sample_dir(sample: dict) -> Path:
    """从 state 中的 sample 解析出样本目录的绝对路径（兼容已持久化的绝对路径）."""
    raw = sample["path"]
    if Path(raw).is_absolute():
        return DATASET_DIR / sample["sample_id"]
    return PROJECT_ROOT / raw


def normalize_real_id(v: Any) -> str:
    return f"{int(v):03d}"


def build_candidates() -> dict[str, list[SampleItem]]:
    out: dict[str, list[SampleItem]] = {
        "real": [],
        "meaningful": [],
        "chaos": [],
        "misleading": [],
    }
    real_meta = load_json(REAL_METADATA)
    for item in real_meta:
        sid = normalize_real_id(item.get("id"))
        sample_dir = DATASET_DIR / sid
        if not sample_dir.is_dir() or not ensure_required_files(sample_dir):
            continue
        out["real"].append(
            SampleItem(
                sample_id=sid,
                data_type="real",
                path=sample_dir_path(sid),
                source="real",
            )
        )

    synth_meta = load_json(SYNTH_METADATA)
    for item in synth_meta:
        sid = str(item.get("id", "")).strip()
        if not sid:
            continue
        sample_dir = DATASET_DIR / sid
        if not sample_dir.is_dir() or not ensure_required_files(sample_dir):
            continue
        source = item.get("source", "")
        sub = item.get("nonsense_subtype", "") or ""
        if source == "synthetic_realistic":
            out["meaningful"].append(
                SampleItem(
                    sample_id=sid,
                    data_type="meaningful",
                    path=sample_dir_path(sid),
                    source="synthetic_realistic",
                )
            )
        elif source == "synthetic_nonsense":
            if sub == "chaos":
                out["chaos"].append(
                    SampleItem(
                        sample_id=sid,
                        data_type="chaos",
                        path=sample_dir_path(sid),
                        source="synthetic_nonsense",
                        nonsense_subtype="chaos",
                    )
                )
            elif sub == "misleading":
                out["misleading"].append(
                    SampleItem(
                        sample_id=sid,
                        data_type="misleading",
                        path=sample_dir_path(sid),
                        source="synthetic_nonsense",
                        nonsense_subtype="misleading",
                    )
                )
    return out


def stratified_pick(candidates: dict[str, list[SampleItem]], counts: dict[str, int], seed: int) -> list[SampleItem]:
    rnd = random.Random(seed)
    picked: list[SampleItem] = []
    for dtype in ("real", "meaningful", "chaos", "misleading"):
        pool = list(candidates.get(dtype, []))
        n = counts.get(dtype, 0)
        if len(pool) < n:
            raise ValueError(f"{dtype} 可用样本不足：需要 {n}，实际 {len(pool)}")
        picked.extend(rnd.sample(pool, n))
    rnd.shuffle(picked)
    return picked


def parse_counts_arg(s: str) -> dict[str, int]:
    # 允许格式: real=250,meaningful=100,chaos=75,misleading=75
    d = dict(DEFAULT_COUNTS)
    if not s.strip():
        return d
    parts = [x.strip() for x in s.split(",") if x.strip()]
    for p in parts:
        k, v = p.split("=")
        k = k.strip()
        if k not in d:
            raise ValueError(f"未知类型: {k}")
        d[k] = int(v.strip())
    return d


def task_key(sample_id: str, model: str) -> str:
    return f"{sample_id}|{model}"


def init_state(samples: list[SampleItem], models: list[str], seed: int, counts: dict[str, int]) -> dict:
    order: list[str] = []
    tasks: dict[str, dict] = {}
    for s in samples:
        for m in models:
            k = task_key(s.sample_id, m)
            order.append(k)
            tasks[k] = {
                "sample_id": s.sample_id,
                "model": m,
                "status": "pending",  # pending|running|done|failed
                "attempts": 0,
                "updated_at": now_ts(),
                "last_error": "",
                "n_questions": 0,
                "n_correct": 0,
            }
    rnd = random.Random(seed + 2026)
    rnd.shuffle(order)

    sample_map = {
        s.sample_id: {
            "sample_id": s.sample_id,
            "data_type": s.data_type,
            "source": s.source,
            "nonsense_subtype": s.nonsense_subtype,
            "path": s.path,
        }
        for s in samples
    }

    return {
        "version": 1,
        "created_at": now_ts(),
        "updated_at": now_ts(),
        "seed": seed,
        "counts": counts,
        "models": models,
        "sample_count": len(samples),
        "task_count": len(order),
        "samples": sample_map,
        "order": order,
        "tasks": tasks,
        "aggregate": {
            "by_model": {},
            "by_data_type": {},
            "total_questions": 0,
            "total_correct": 0,
        },
    }


def rebuild_aggregate_from_tasks(state: dict) -> None:
    by_model: dict[str, dict[str, int]] = {}
    by_dtype: dict[str, dict[str, int]] = {}
    total_q = 0
    total_c = 0
    for t in state["tasks"].values():
        if t.get("status") != "done":
            continue
        model = t["model"]
        sample = state["samples"][t["sample_id"]]
        dtype = sample["data_type"]
        q = int(t.get("n_questions", 0))
        c = int(t.get("n_correct", 0))
        total_q += q
        total_c += c
        bm = by_model.setdefault(model, {"q": 0, "c": 0})
        bm["q"] += q
        bm["c"] += c
        bd = by_dtype.setdefault(dtype, {"q": 0, "c": 0})
        bd["q"] += q
        bd["c"] += c
    state["aggregate"] = {
        "by_model": by_model,
        "by_data_type": by_dtype,
        "total_questions": total_q,
        "total_correct": total_c,
    }


def save_state(out_dir: Path, state: dict) -> None:
    state["updated_at"] = now_ts()
    save_json(out_dir / STATE_FILE, state)


def load_state(out_dir: Path) -> dict:
    state = load_json(out_dir / STATE_FILE)
    # 将已持久化的绝对路径规范为相对路径
    for s in state.get("samples", {}).values():
        if Path(s["path"]).is_absolute():
            s["path"] = sample_dir_path(s["sample_id"])
    return state


def probe_one_model(model: str, img_path: Path, api_key: str) -> tuple[bool, str]:
    data_url = image_to_data_url(img_path)
    prompt = "请只回复一个大写字母 A。不要任何其他文字。"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "max_tokens": 16,
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        msg = r.json().get("choices", [{}])[0].get("message", {})
        txt = message_text(msg).strip().upper()
        ok = txt.startswith("A")
        return ok, txt[:80]
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def run_probe(out_dir: Path, state: dict, strict: bool, api_key: str) -> tuple[list[str], list[str]]:
    sample_any = next(iter(state["samples"].values()))
    img_path = resolve_sample_dir(sample_any) / "diagram.png"
    passed, failed = [], []
    log(out_dir, "开始模型预检（每次 run 前强制执行）...")
    for model in state["models"]:
        ok, detail = probe_one_model(model, img_path, api_key)
        rec = {
            "time": now_ts(),
            "model": model,
            "ok": ok,
            "detail": detail,
        }
        append_jsonl(out_dir / PROBE_HISTORY, rec)
        if ok:
            passed.append(model)
            log(out_dir, f"  [probe][OK] {model}")
        else:
            failed.append(model)
            log(out_dir, f"  [probe][FAIL] {model} :: {detail}")
        time.sleep(0.4)
    log(out_dir, f"预检结果: {len(passed)}/{len(state['models'])} 通过")
    if strict and failed:
        log(out_dir, "严格模式启用：存在预检失败模型，已中止正式评测。")
    return passed, failed


def build_batch_prompt(qa_list: list[dict]) -> str:
    blocks = []
    for qidx, qa in enumerate(qa_list):
        opts = qa.get("options", [])
        opt_text = "\n".join(opts)
        blocks.append(f"Q{qidx}. {qa.get('question', '')}\n{opt_text}")
    questions_block = "\n\n".join(blocks)
    n = len(qa_list)
    return f"""你将看到一张流程图/架构图，以及该图对应的 {n} 道单选题。请逐题作答。

【必须遵守】
- 你的回复必须且只能是一个 JSON 数组，长度必须等于 {n}。
- 数组中的每个元素必须是一个大写字母字符串："A"、"B"、"C" 或 "D"。
- 第 i 个元素对应 Q{{i}} 的答案。
- 禁止输出任何解释、标点、换行、代码块或其它文字。

题目如下：
{questions_block}

请直接输出 JSON 数组："""


def answer_batch(model: str, img_path: Path, qa_list: list[dict], api_key: str, max_attempts: int = 3) -> tuple[list[str], str]:
    prompt = build_batch_prompt(qa_list)
    data_url = image_to_data_url(img_path)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "max_tokens": 256,
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    expected_n = len(qa_list)
    last_err = ""
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=150)
            if r.status_code != 200:
                last_err = f"HTTP {r.status_code}: {r.text[:200]}"
                time.sleep(2)
                continue
            msg = r.json().get("choices", [{}])[0].get("message", {})
            txt = message_text(msg)
            answers = parse_batch_answers(txt, expected_n=expected_n)
            if answers:
                return answers, txt
            last_err = f"格式解析失败: {txt[:180]}"
            time.sleep(2)
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            time.sleep(2)
    return [], last_err


def qa_correct_letter(qa: dict) -> str:
    opts = qa.get("options", [])
    ci = int(qa.get("correct_index", 0) or 0)
    if not opts or ci < 0 or ci >= len(opts):
        return "A"
    s = str(opts[ci]).strip().upper()
    return s[:1] if s and s[:1] in "ABCD" else "A"


def status_summary(state: dict) -> dict[str, int]:
    s = {"pending": 0, "running": 0, "done": 0, "failed": 0}
    for t in state["tasks"].values():
        st = t.get("status", "pending")
        if st not in s:
            st = "pending"
        s[st] += 1
    return s


def print_periodic_stats(out_dir: Path, state: dict, processed_this_run: int, started_at: float) -> None:
    """
    阶段性输出更接近 pilot_v3/pilot_v4 的多维统计：
    - 进度 & ETA
    - 按数据来源类型
    - 按模型
    - 按模型 × 数据来源
    - 按模型 × 题目类型
    """
    ss = status_summary(state)
    done = ss["done"]
    total = state["task_count"]
    elapsed = max(1.0, time.time() - started_at)
    speed = processed_this_run / elapsed  # tasks/sec
    remain = ss["pending"] + ss["failed"] + ss["running"]
    eta_sec = int(remain / speed) if speed > 0 else -1
    eta = f"{eta_sec // 3600:02d}:{(eta_sec % 3600) // 60:02d}:{eta_sec % 60:02d}" if eta_sec >= 0 else "--:--:--"

    # 为了避免累计误差，这里基于 tasks 重新聚合一遍（不修改 state，只做只读汇总）
    by_model: dict[str, list[int]] = {}
    by_data_type: dict[str, list[int]] = {}
    by_model_data: dict[tuple[str, str], list[int]] = {}
    by_model_type: dict[tuple[str, str], list[int]] = {}
    total_q = 0
    total_c = 0

    for t in state["tasks"].values():
        if t.get("status") != "done":
            continue
        sample = state["samples"][t["sample_id"]]
        model = t["model"]
        dtype = sample["data_type"]
        q = int(t.get("n_questions", 0))
        c = int(t.get("n_correct", 0))
        if q <= 0:
            continue
        total_q += q
        total_c += c
        by_model.setdefault(model, []).extend([1] * c + [0] * (q - c))
        by_data_type.setdefault(dtype, []).extend([1] * c + [0] * (q - c))
        by_model_data.setdefault((model, dtype), []).extend([1] * c + [0] * (q - c))

    # 为了能按题型拆分，需要从结果文件读取；但频繁读盘成本略高，这里只基于 state 的粗汇总
    # 若后续需要更细粒度分析，可额外写一个离线分析脚本。

    acc = (total_c / total_q * 100) if total_q else 0.0
    log(
        out_dir,
        f"[进度] done={done}/{total}, pending={ss['pending']}, failed={ss['failed']}, "
        f"本轮处理={processed_this_run}, 累计题目准确率={acc:.2f}%, ETA~{eta}",
    )

    def _acc(vals: list[int]) -> float:
        return (sum(vals) / len(vals) * 100) if vals else 0.0

    # 按数据来源
    if by_data_type:
        parts = []
        for dtype in ("real", "meaningful", "chaos", "misleading"):
            vals = by_data_type.get(dtype)
            if not vals:
                continue
            parts.append(f"{dtype}: {_acc(vals):.1f}% ({sum(vals)}/{len(vals)})")
        if parts:
            log(out_dir, "[按数据来源] " + " | ".join(parts))

    # 按模型
    if by_model:
        lines = []
        for m in state["models"]:
            vals = by_model.get(m)
            if not vals:
                continue
            lines.append(f"{m}: {_acc(vals):.1f}% ({sum(vals)}/{len(vals)})")
        if lines:
            log(out_dir, "[按模型] " + " | ".join(lines))

    # 按模型 × 数据来源（核心表精简版）
    if by_model_data:
        rows = []
        for (m, dt), vals in sorted(by_model_data.items(), key=lambda x: (x[0][0], x[0][1])):
            rows.append(f"{m} | {dt}: {_acc(vals):.1f}% ({sum(vals)}/{len(vals)})")
        if rows:
            log(out_dir, "[按模型 × 数据来源]")
            for r in rows:
                log(out_dir, "  " + r)


def cmd_init(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / STATE_FILE
    if state_path.exists() and not args.force:
        print(f"state 已存在：{state_path}，如需重建请加 --force")
        return 1

    counts = parse_counts_arg(args.counts)
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("样本总数必须 > 0")
    if total != args.total:
        raise ValueError(f"--total={args.total} 与 counts 总和 {total} 不一致")

    candidates = build_candidates()
    picked = stratified_pick(candidates, counts, seed=args.seed)
    state = init_state(samples=picked, models=MODELS, seed=args.seed, counts=counts)
    save_state(out_dir, state)
    save_json(out_dir / SELECTION_FILE, [s.__dict__ for s in picked])

    # 初始化输出文件
    for fn in (RESULTS_JSONL, RESPONSES_JSONL, PROBE_HISTORY):
        (out_dir / fn).write_text("", encoding="utf-8")
    (out_dir / LOG_FILE).write_text("", encoding="utf-8")
    pause = out_dir / PAUSE_FILE
    if pause.exists():
        pause.unlink()

    log(out_dir, f"初始化完成: out={out_dir}")
    log(out_dir, f"样本总数={len(picked)}，任务总数={state['task_count']}（{len(MODELS)} 模型）")
    log(out_dir, f"分层配额: {counts}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    state = load_state(out_dir)
    rebuild_aggregate_from_tasks(state)
    ss = status_summary(state)
    print(json.dumps(
        {
            "out_dir": str(out_dir),
            "sample_count": state["sample_count"],
            "task_count": state["task_count"],
            "status": ss,
            "aggregate": state["aggregate"],
            "paused": (out_dir / PAUSE_FILE).exists(),
            "updated_at": state.get("updated_at"),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    (out_dir / PAUSE_FILE).write_text("pause\n", encoding="utf-8")
    print(f"已写入暂停标记: {out_dir / PAUSE_FILE}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    p = out_dir / PAUSE_FILE
    if p.exists():
        p.unlink()
    print("已移除暂停标记，可继续 run。")
    return 0


def cmd_retry_failed(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir).resolve()
    state = load_state(out_dir)
    n = 0
    for t in state["tasks"].values():
        if t.get("status") == "failed":
            t["status"] = "pending"
            t["last_error"] = ""
            t["updated_at"] = now_ts()
            n += 1
    save_state(out_dir, state)
    print(f"已将 {n} 个 failed 任务重置为 pending。")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    global STOP_REQUESTED
    STOP_REQUESTED = False

    out_dir = Path(args.out_dir).resolve()
    state = load_state(out_dir)
    api_key = get_api_key()
    if not api_key:
        print("未找到 OPENROUTER_API_KEY（请设置环境变量或在项目根目录 .env 中配置，参考 .env.example）")
        return 2

    if (out_dir / PAUSE_FILE).exists():
        print(f"检测到暂停标记：{out_dir / PAUSE_FILE}。请先 resume。")
        return 1

    # 每次 run 前强制预检
    passed, failed = run_probe(out_dir, state, strict=not args.allow_partial, api_key=api_key)
    if failed and not args.allow_partial:
        return 3
    active_models = passed if args.allow_partial else state["models"]
    if not active_models:
        log(out_dir, "无可用模型，退出。")
        return 3

    # 若 allow_partial，未通过模型对应任务保持 pending，不会被执行
    active_set = set(active_models)
    ss0 = status_summary(state)
    log(
        out_dir,
        f"开始执行: done={ss0['done']}, pending={ss0['pending']}, failed={ss0['failed']}, active_models={len(active_models)}",
    )

    started_at = time.time()
    processed_this_run = 0
    last_report = time.time()
    report_every_n = max(1, int(args.log_every))

    results_path = out_dir / RESULTS_JSONL
    responses_path = out_dir / RESPONSES_JSONL

    try:
        for k in state["order"]:
            if STOP_REQUESTED:
                raise GracefulStop("收到中断信号，准备安全退出。")
            if (out_dir / PAUSE_FILE).exists():
                raise GracefulStop("检测到暂停标记，准备安全暂停。")

            t = state["tasks"][k]
            model = t["model"]
            if model not in active_set:
                continue
            if t["status"] == "done":
                continue
            if t["status"] == "running":
                # 上次中断遗留 running，重置后继续
                t["status"] = "pending"

            sample = state["samples"][t["sample_id"]]
            sample_dir = resolve_sample_dir(sample)
            qa_path = sample_dir / "qa.json"
            img_path = sample_dir / "diagram.png"
            if not qa_path.exists() or not img_path.exists():
                t["status"] = "failed"
                t["last_error"] = "缺少 qa.json 或 diagram.png"
                t["updated_at"] = now_ts()
                save_state(out_dir, state)
                continue

            qa_list = load_json(qa_path)
            if not isinstance(qa_list, list) or not qa_list:
                t["status"] = "failed"
                t["last_error"] = "qa.json 非有效数组"
                t["updated_at"] = now_ts()
                save_state(out_dir, state)
                continue

            t["status"] = "running"
            t["attempts"] = int(t.get("attempts", 0)) + 1
            t["updated_at"] = now_ts()
            save_state(out_dir, state)

            answers, raw_text_or_err = answer_batch(
                model=model,
                img_path=img_path,
                qa_list=qa_list,
                api_key=api_key,
                max_attempts=args.max_attempts,
            )

            if answers and len(answers) == len(qa_list):
                n_correct = 0
                for qidx, qa in enumerate(qa_list):
                    correct_letter = qa_correct_letter(qa)
                    pred = answers[qidx]
                    is_ok = int(pred == correct_letter)
                    n_correct += is_ok
                    rec = {
                        "time": now_ts(),
                        "sample_id": sample["sample_id"],
                        "data_type": sample["data_type"],
                        "nonsense_subtype": sample.get("nonsense_subtype", ""),
                        "model": model,
                        "qidx": qidx,
                        "type": qa.get("type", "unknown"),
                        "difficulty": qa.get("difficulty", "unknown"),
                        "correct_letter": correct_letter,
                        "predicted": pred,
                        "correct": is_ok,
                        "protocol": "batch_per_image",
                    }
                    append_jsonl(results_path, rec)
                append_jsonl(
                    responses_path,
                    {
                        "time": now_ts(),
                        "sample_id": sample["sample_id"],
                        "data_type": sample["data_type"],
                        "model": model,
                        "answers": answers,
                        "raw_text": raw_text_or_err[:5000],
                    },
                )
                t["status"] = "done"
                t["last_error"] = ""
                t["n_questions"] = len(qa_list)
                t["n_correct"] = n_correct

                # 增量更新聚合
                agg = state["aggregate"]
                agg["total_questions"] = int(agg.get("total_questions", 0)) + len(qa_list)
                agg["total_correct"] = int(agg.get("total_correct", 0)) + n_correct
                bm = agg.setdefault("by_model", {}).setdefault(model, {"q": 0, "c": 0})
                bm["q"] += len(qa_list)
                bm["c"] += n_correct
                dt = sample["data_type"]
                bd = agg.setdefault("by_data_type", {}).setdefault(dt, {"q": 0, "c": 0})
                bd["q"] += len(qa_list)
                bd["c"] += n_correct
            else:
                t["status"] = "failed"
                t["last_error"] = raw_text_or_err[:500]
                t["n_questions"] = 0
                t["n_correct"] = 0

            t["updated_at"] = now_ts()
            save_state(out_dir, state)
            processed_this_run += 1

            if processed_this_run % report_every_n == 0 or (time.time() - last_report) > 120:
                print_periodic_stats(out_dir, state, processed_this_run, started_at)
                last_report = time.time()

            time.sleep(args.sleep_between)

    except GracefulStop as e:
        log(out_dir, str(e))
    except Exception as e:  # noqa: BLE001
        log(out_dir, f"运行异常终止: {e}")
        save_state(out_dir, state)
        return 4

    # 收尾输出
    rebuild_aggregate_from_tasks(state)
    save_state(out_dir, state)
    ss = status_summary(state)
    agg = state["aggregate"]
    tq = int(agg.get("total_questions", 0))
    tc = int(agg.get("total_correct", 0))
    acc = (tc / tq * 100) if tq else 0.0
    log(
        out_dir,
        f"本轮结束: done={ss['done']}/{state['task_count']}, pending={ss['pending']}, "
        f"failed={ss['failed']}, 累计准确率={acc:.2f}%",
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FlowSight 500样本多模型评测（可暂停/续跑/重试）")
    p.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="输出目录（默认 benchmark_run）")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_init = sub.add_parser("init", help="初始化抽样与任务状态")
    sp_init.add_argument("--seed", type=int, default=DEFAULT_SEED)
    sp_init.add_argument("--total", type=int, default=500)
    sp_init.add_argument(
        "--counts",
        default="real=250,meaningful=100,chaos=75,misleading=75",
        help="分层配额，格式: real=250,meaningful=100,chaos=75,misleading=75",
    )
    sp_init.add_argument("--force", action="store_true", help="覆盖已有 state")

    sp_run = sub.add_parser("run", help="执行/继续执行评测")
    sp_run.add_argument("--max-attempts", type=int, default=3, help="每任务最大重试次数")
    sp_run.add_argument("--sleep-between", type=float, default=0.2, help="任务间休眠秒数")
    sp_run.add_argument("--log-every", type=int, default=20, help="每处理多少任务打印一次统计")
    sp_run.add_argument("--allow-partial", action="store_true", help="预检失败时仍运行通过的模型")

    sub.add_parser("status", help="查看状态与累计统计")
    sub.add_parser("pause", help="写入暂停标记（当前 run 会在下一个任务点停下）")
    sub.add_parser("resume", help="移除暂停标记")
    sub.add_parser("retry_failed", help="将 failed 任务重置为 pending")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.cmd == "init":
        return cmd_init(args)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "pause":
        return cmd_pause(args)
    if args.cmd == "resume":
        return cmd_resume(args)
    if args.cmd == "retry_failed":
        return cmd_retry_failed(args)
    print(f"未知命令: {args.cmd}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

