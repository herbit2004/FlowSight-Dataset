#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pilot V3：按数据来源类型抽样 × 多模型评测 × 实验有效性分析。

- 四类数据各随机抽 10 条：真实(real)、LLM 有意义(meaningful)、LLM 完全混乱(chaos)、LLM 误导(misleading)。
- 共 40 条，复制到 pilot_v3/out/，命名 real_00..09, meaningful_00..09, chaos_00..09, misleading_00..09。
- manifest.json 记录每目录的 data_type 与 source_id，便于按类型聚合。
- QA 生成与评测逻辑复用 pilot_v2（分类型分难度、多模型并行）；报告按 data_type 与 model 分层。
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
OUT_DIR = PROJECT_ROOT / "pilot_v3" / "out"
REAL_METADATA = DATASET_DIR / "metadata.json"
SYNTHETIC_METADATA = DATASET_DIR / "synthetic_metadata.json"
SAMPLE_PER_TYPE = 10
SEED = 42

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MERMAID_INK_BASE = "https://mermaid.ink/img/{encoded}?type=png"

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


def _get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    try:
        with open(PROJECT_ROOT / "build_dataset.py", encoding="utf-8") as f:
            m = re.search(r'OPENROUTER_API_KEY\s*=\s*["\']([^"\']+)["\']', f.read())
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""


API_KEY = _get_api_key()
LOG_PATH = OUT_DIR.parent / "pilot_v3.log"
MANIFEST_PATH = OUT_DIR / "manifest.json"
EVAL_JSONL_PATH = OUT_DIR / "eval_results.jsonl"
PROBE_OK_PATH = OUT_DIR / "probe_ok.json"


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


# ── 1. 按类型抽样并准备样本 ─────────────────────────────────────────────────
def _load_real_ids() -> list[str]:
    if not REAL_METADATA.exists():
        return []
    data = json.loads(REAL_METADATA.read_text(encoding="utf-8"))
    ids = []
    for item in data:
        fid = item.get("id")
        if fid is not None:
            ids.append(f"{int(fid):03d}")
    return ids


def _load_synthetic_by_type() -> tuple[list[str], list[str], list[str]]:
    """返回 (meaningful_ids, chaos_ids, misleading_ids)。"""
    meaningful, chaos, misleading = [], [], []
    if not SYNTHETIC_METADATA.exists():
        return meaningful, chaos, misleading
    data = json.loads(SYNTHETIC_METADATA.read_text(encoding="utf-8"))
    for item in data:
        sid = item.get("id", "")
        if sid.startswith("meaningful_"):
            meaningful.append(sid)
        elif sid.startswith("nonsense_"):
            st = item.get("nonsense_subtype", "")
            if st == "chaos":
                chaos.append(sid)
            elif st == "misleading":
                misleading.append(sid)
    return meaningful, chaos, misleading


def ensure_samples() -> tuple[list[Path], list[dict]]:
    """四类各随机抽 SAMPLE_PER_TYPE 条，复制到 out/<data_type>_<ii>/，返回 (sample_dirs, manifest)。"""
    random.seed(SEED)
    real_ids = _load_real_ids()
    meaningful_ids, chaos_ids, misleading_ids = _load_synthetic_by_type()

    def sample(ids: list[str], n: int) -> list[str]:
        if len(ids) <= n:
            return list(ids)
        return random.sample(ids, n)

    real_sel = sample(real_ids, SAMPLE_PER_TYPE)
    meaningful_sel = sample(meaningful_ids, SAMPLE_PER_TYPE)
    chaos_sel = sample(chaos_ids, SAMPLE_PER_TYPE)
    misleading_sel = sample(misleading_ids, SAMPLE_PER_TYPE)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    sample_dirs = []

    for i, sid in enumerate(real_sel):
        slot = f"real_{i:02d}"
        src = DATASET_DIR / sid
        dst = OUT_DIR / slot
        if not src.exists():
            log(f"  跳过 {slot}: 源目录不存在 {src}")
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("diagram.mmd", "description.txt"):
            f = src / name
            if f.exists():
                (dst / name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
        png_src = src / "diagram.png"
        if png_src.exists():
            (dst / "diagram.png").write_bytes(png_src.read_bytes())
        if (dst / "diagram.png").exists():
            manifest.append({"dir": slot, "data_type": "real", "source_id": sid})
            sample_dirs.append(dst)

    for i, sid in enumerate(meaningful_sel):
        slot = f"meaningful_{i:02d}"
        src = DATASET_DIR / sid
        dst = OUT_DIR / slot
        if not src.exists():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("diagram.mmd", "description.txt"):
            f = src / name
            if f.exists():
                (dst / name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
        if (src / "diagram.png").exists():
            (dst / "diagram.png").write_bytes((src / "diagram.png").read_bytes())
        if (dst / "diagram.png").exists():
            manifest.append({"dir": slot, "data_type": "meaningful", "source_id": sid})
            sample_dirs.append(dst)

    for i, sid in enumerate(chaos_sel):
        slot = f"chaos_{i:02d}"
        src = DATASET_DIR / sid
        dst = OUT_DIR / slot
        if not src.exists():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("diagram.mmd", "description.txt"):
            f = src / name
            if f.exists():
                (dst / name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
        if (src / "diagram.png").exists():
            (dst / "diagram.png").write_bytes((src / "diagram.png").read_bytes())
        if (dst / "diagram.png").exists():
            manifest.append({"dir": slot, "data_type": "chaos", "source_id": sid})
            sample_dirs.append(dst)

    for i, sid in enumerate(misleading_sel):
        slot = f"misleading_{i:02d}"
        src = DATASET_DIR / sid
        dst = OUT_DIR / slot
        if not src.exists():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("diagram.mmd", "description.txt"):
            f = src / name
            if f.exists():
                (dst / name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
        if (src / "diagram.png").exists():
            (dst / "diagram.png").write_bytes((src / "diagram.png").read_bytes())
        if (dst / "diagram.png").exists():
            manifest.append({"dir": slot, "data_type": "misleading", "source_id": sid})
            sample_dirs.append(dst)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return sample_dirs, manifest


# ── 2. QA 生成（与 pilot_v2 一致）────────────────────────────────────────────
def _chat(messages: list, max_tokens: int = 2800, temperature: float = 0.3) -> str | None:
    if not API_KEY:
        return None
    for _ in range(3):
        try:
            r = requests.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={"model": "google/gemini-2.0-flash-001", "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
                timeout=90,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            time.sleep(4)
        except Exception as e:
            log(f"  [chat] {e}")
            time.sleep(4)
    return None


def generate_qa(sample_dir: Path) -> bool:
    mmd_path = sample_dir / "diagram.mmd"
    desc_path = sample_dir / "description.txt"
    if not mmd_path.exists() or not desc_path.exists():
        return False
    mmd = mmd_path.read_text(encoding="utf-8")
    desc = desc_path.read_text(encoding="utf-8")
    # 提示词与 pilot_v2 完全一致，保证题目设计强度与区分度不弱于 v2
    prompt = f"""你为一张流程图/架构图生成**能区分不同多模态模型能力**的评测选择题。目标：让 8B、30B、235B 以及 instruct 与 thinking 之间在准确率上拉开差距，因此题目不能太简单，需要触及多步推理、易混选项、长链与否定理解。

要求：
1. 共 {QA_PER_SAMPLE} 道题，每道题必须标注 type 与 difficulty：
   - type：factual（事实题）、reasoning（多步推理）、negation（否定/「以下哪个不是」）。
   - difficulty：easy（尽量少）、medium、hard（多步/易混/长链，占比要多）。
2. 类型与难度分布：至少 2 道 reasoning、1 道 negation；easy 最多 1 道，medium 至少 2 道，hard 至少 2 道。题目表述清晰，答案唯一，仅凭图可答。
3. **题目设计要能拉开模型差距**，请包含：
   - **多跳推理**：例如「从节点 X 到节点 Y 必须经过的中间节点是」「若某分支选 No，最终会到达哪一节点」「完成 A 之后、在 B 之前，必须经过哪一步」。
   - **易混选项**：至少 2 道题的选项中，有两个选项在图中都出现或表述相近，需仔细看图才能区分；或问「可以并行进行的两个步骤是」等需区分顺序/并行的题。
   - **长链/远距离**：涉及图中相距较远的节点（非直接相邻），如「从流程起点到终点，按顺序会经过以下哪组节点」「图中与节点 X 相距最远的一步是」。
   - **否定题**：题干明确「以下哪个不是」「图中未出现的环节是」；干扰项要是 plausible 的术语（图中或领域常见词），避免一眼排除。
4. 每道题 4 个选项 A/B/C/D，正确选项唯一；干扰项合理且有一定迷惑性。
5. 只输出一个 JSON 数组，无其他内容。每项格式：
   {{"question": "题目", "options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"], "correct_index": 0, "type": "factual|reasoning|negation", "difficulty": "easy|medium|hard"}}

Mermaid 源码：
```mermaid
{mmd}
```

图的描述（供出题对照，答案须能从图中得出）：
---
{desc[:7500]}
---
输出 JSON 数组："""
    out = _chat([{"role": "user", "content": prompt}])
    if not out:
        return False
    text = out.strip()
    if "```" in text:
        m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
        if m:
            text = m.group(1).strip()
    for start, end in [("[", "]"), ("{", "}")]:
        i = text.find(start)
        if i < 0:
            continue
        j = text.rfind(end)
        if j <= i:
            continue
        raw = text[i : j + 1]
        raw = re.sub(r",\s*]", "]", raw)
        raw = re.sub(r",\s*}", "}", raw)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            try:
                data = json.loads(raw.replace("'", '"'))
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
            t = (item.get("type") or item.get("question_type") or "factual").lower()
            d = (item.get("difficulty") or item.get("diff") or "medium").lower()
            if t not in QA_TYPES:
                t = "factual"
            if d not in QA_DIFFICULTIES:
                d = "medium"
            if q and opts and 0 <= idx < len(opts):
                qa_list.append({"question": q, "options": list(opts), "correct_index": int(idx), "type": t, "difficulty": d})
        if qa_list:
            (sample_dir / "qa.json").write_text(json.dumps(qa_list, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
    return False


def run_qa_generation(sample_dirs: list[Path], overwrite: bool = False) -> None:
    for d in sample_dirs:
        if (d / "qa.json").exists() and not overwrite:
            log(f"  已有 qa {d.name}，跳过")
            continue
        if (d / "qa.json").exists() and overwrite:
            (d / "qa.json").unlink()
        if generate_qa(d):
            log(f"  QA {d.name} OK")
        else:
            log(f"  QA {d.name} FAIL")
        time.sleep(1.5)


# ── 3. 预检与评测 ───────────────────────────────────────────────────────────
def image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('utf-8')}"


def _parse_message_to_letter(msg: dict) -> str:
    raw = msg.get("content")
    if isinstance(raw, list):
        text = " ".join(
            item.get("text", item.get("content", "")) or ""
            for item in raw if isinstance(item, dict) and item.get("type") == "text"
        )
    else:
        text = raw or msg.get("reasoning") or msg.get("refusal") or ""
    text = str(text or "").strip().upper()
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


def _answer_one(image_path: Path, question: str, options: list[str], model: str, correct_letter: str) -> tuple[str, str, int]:
    if not API_KEY:
        return model, "", 0
    opt_text = "\n".join(options)
    prompt = f"""根据所给流程图/架构图作答下面的单选题。

题目：{question}

选项：
{opt_text}

【必须遵守】你的回复必须且只能是以下四个大写字母之一：A、B、C 或 D。禁止输出任何解释、标点、换行或其它字符。
请直接输出一个字母："""
    data_url = image_to_data_url(image_path)
    payload_base = {
        "model": model,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": data_url}}]}],
        "max_tokens": 48,
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            r = requests.post(OPENROUTER_URL, headers=headers, json=payload_base, timeout=90)
            if r.status_code != 200:
                if attempt < 2:
                    time.sleep(2)
                continue
            msg = r.json().get("choices", [{}])[0].get("message", {})
            pred = _parse_message_to_letter(msg)
            if pred:
                return model, pred, 1 if pred == correct_letter else 0
            if attempt < 2:
                time.sleep(2)
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                log(f"    [answer] {model} 异常: {e}")
    return model, "", 0


def run_eval(sample_dirs: list[Path], manifest: list[dict]) -> dict:
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
            for qidx, qa in enumerate(qa_list):
                opts = qa.get("options", [])
                ci = qa.get("correct_index", 0)
                if not opts or ci >= len(opts):
                    continue
                correct_letter = (opts[ci].strip()[0] if opts[ci].strip() else "A").upper()

                def task(m: str):
                    return _answer_one(img_path, qa["question"], opts, m, correct_letter)

                with ThreadPoolExecutor(max_workers=max_workers) as ex:
                    futures = {ex.submit(task, m): m for m in models_to_use}
                    for fut in as_completed(futures):
                        m, pred, correct = fut.result()
                        rec = {
                            "sample": sample_dir.name,
                            "data_type": data_type,
                            "qidx": qidx,
                            "type": qa.get("type", "factual"),
                            "difficulty": qa.get("difficulty", "medium"),
                            "model": m,
                            "correct_letter": correct_letter,
                            "predicted": pred,
                            "correct": correct,
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

    lines = ["=== Pilot V3 汇总（四类数据 × 多模型）===\n"]
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


# ── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    import sys
    step = (sys.argv[1:] or ["all"])[0].lower()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if step in ("all", "eval") and LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")

    log("Pilot V3 开始（四类各 %d 条，共 40 条）" % SAMPLE_PER_TYPE)
    sample_dirs, manifest = ensure_samples()
    log("样本数: %d，manifest 已写入 %s" % (len(sample_dirs), MANIFEST_PATH.name))

    if step == "qa_regen":
        run_qa_generation(sample_dirs, overwrite=True)
    elif step in ("all", "qa"):
        run_qa_generation(sample_dirs, overwrite=False)
    if step == "probe":
        passed = probe_models(sample_dirs)
        (OUT_DIR / "probe_ok.json").write_text(
            json.dumps({"passed": passed, "failed": [m for m in MODELS if m not in passed]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        log("通过 %d/%d" % (len(passed), len(MODELS)))
    if step in ("all", "eval"):
        raw = run_eval(sample_dirs, manifest)
        (OUT_DIR / "eval_results.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        report = aggregate_report(raw)
        log(report)
        (OUT_DIR / "report.txt").write_text(report, encoding="utf-8")

    log("Pilot V3 结束")


if __name__ == "__main__":
    main()
