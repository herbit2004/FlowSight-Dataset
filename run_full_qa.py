#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量 dataset 的 QA 生成（v3 同款提示词与逻辑），支持灵活打断、重试、暂停继续、补全。

- 顺序：真实 000–499 → meaningful_000–199 → nonsense_000–149(chaos) → nonsense_150–299(misleading)，共 1000 条。
- 输出：qa.json 写入 dataset/<id>/，不复制样本。
- 默认：跳过已有 qa.json 的目录（中断后直接再运行即可继续）。
- --retry-failed：仅对进度文件中记录的失败 id 重试。
- --overwrite：强制重新生成已有 qa.json 的样本。
- --start N / --limit M：从第 N 条起、最多处理 M 条（便于分段跑）。
- --dry-run：只打印将处理的 id 列表并退出。
- 进度文件：full_qa_progress.json（completed_ids、failed_ids、updated_at），每处理一条即更新。
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import requests

from env_config import load_env, get_openrouter_api_key

PROJECT_ROOT = Path(__file__).resolve().parent
load_env()
API_KEY = get_openrouter_api_key()

DATASET_DIR = PROJECT_ROOT / "dataset"
REAL_METADATA = DATASET_DIR / "metadata.json"
SYNTHETIC_METADATA = DATASET_DIR / "synthetic_metadata.json"
PROGRESS_PATH = PROJECT_ROOT / "full_qa_progress.json"
LOG_PATH = PROJECT_ROOT / "full_qa.log"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
QA_TYPES = ("factual", "reasoning", "negation")
QA_DIFFICULTIES = ("easy", "medium", "hard")
QA_PER_SAMPLE = 6


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{ts}] {msg}\n"
    try:
        print(msg, flush=True)
    except Exception:
        pass
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def build_ordered_ids() -> list[str]:
    """固定顺序：real 000–499, meaningful_000–199, nonsense_000–149, nonsense_150–299。"""
    ids = []
    # 真实 500
    if REAL_METADATA.exists():
        data = json.loads(REAL_METADATA.read_text(encoding="utf-8"))
        for item in data:
            fid = item.get("id")
            if fid is not None:
                ids.append(f"{int(fid):03d}")
    else:
        ids.extend(f"{i:03d}" for i in range(500))
    # 合成：meaningful 200
    ids.extend(f"meaningful_{i:03d}" for i in range(200))
    # nonsense 0–149 (chaos), 150–299 (misleading)
    ids.extend(f"nonsense_{i:03d}" for i in range(300))
    return ids


def load_progress() -> dict:
    if not PROGRESS_PATH.exists():
        return {"completed_ids": [], "failed_ids": [], "updated_at": None}
    try:
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"completed_ids": [], "failed_ids": [], "updated_at": None}


def save_progress(progress: dict) -> None:
    progress["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    PROGRESS_PATH.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def _chat(messages: list, max_tokens: int = 2800, temperature: float = 0.3) -> str | None:
    if not API_KEY:
        return None
    for _ in range(3):
        try:
            r = requests.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "google/gemini-2.0-flash-001",
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=90,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            time.sleep(4)
        except Exception as e:
            log(f"    [chat] {e}")
            time.sleep(4)
    return None


def generate_qa(sample_dir: Path) -> bool:
    """与 pilot_v3 同款：读 diagram.mmd + description.txt，写 qa.json。"""
    mmd_path = sample_dir / "diagram.mmd"
    desc_path = sample_dir / "description.txt"
    if not mmd_path.exists() or not desc_path.exists():
        return False
    mmd = mmd_path.read_text(encoding="utf-8")
    desc = desc_path.read_text(encoding="utf-8")
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


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="全量 dataset QA 生成（v3 逻辑），支持中断/继续/重试/补全")
    parser.add_argument("--retry-failed", action="store_true", help="仅对上次记录的失败 id 重试")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有 qa.json 重新生成")
    parser.add_argument("--start", type=int, default=0, help="从第 N 条开始（0-based）")
    parser.add_argument("--limit", type=int, default=0, help="最多处理 M 条，0 表示不限制")
    parser.add_argument("--dry-run", action="store_true", help="只打印将处理的 id 并退出")
    args = parser.parse_args()

    ordered = build_ordered_ids()
    progress = load_progress()
    completed_set = set(progress.get("completed_ids", []))
    failed_list = list(progress.get("failed_ids", []))

    if args.retry_failed:
        to_process = [sid for sid in failed_list if (DATASET_DIR / sid).exists()]
        log("仅重试失败: %d 条" % len(to_process))
    else:
        to_process = []
        for i, sid in enumerate(ordered):
            if i < args.start:
                continue
            if args.limit and len(to_process) >= args.limit:
                break
            sample_dir = DATASET_DIR / sid
            if not sample_dir.is_dir():
                continue
            has_qa = (sample_dir / "qa.json").exists()
            if has_qa and not args.overwrite:
                continue
            to_process.append(sid)
        log("待处理: %d 条 (start=%s, limit=%s, overwrite=%s)" % (len(to_process), args.start, args.limit or "无", args.overwrite))

    if args.dry_run:
        for sid in to_process:
            print(sid)
        log("dry-run 共 %d 条" % len(to_process))
        return

    if not API_KEY:
        log("错误: 未设置 OPENROUTER_API_KEY（请在项目根目录 .env 中配置，参考 .env.example）")
        return

    done = 0
    new_failed = []
    for sid in to_process:
        sample_dir = DATASET_DIR / sid
        if args.overwrite and (sample_dir / "qa.json").exists():
            (sample_dir / "qa.json").unlink()
        if generate_qa(sample_dir):
            done += 1
            completed_set.add(sid)
            if sid in failed_list:
                failed_list.remove(sid)
            log("  OK  %s" % sid)
        else:
            failed_list.append(sid) if sid not in failed_list else None
            new_failed.append(sid)
            log("  FAIL %s" % sid)
        progress["completed_ids"] = sorted(completed_set)
        progress["failed_ids"] = list(dict.fromkeys(failed_list))
        save_progress(progress)
        time.sleep(1.5)

    log("本轮完成: %d 成功, %d 失败; 累计完成 %d, 失败列表 %d" % (done, len(new_failed), len(completed_set), len(failed_list)))


if __name__ == "__main__":
    main()
