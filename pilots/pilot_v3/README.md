# Pilot V3：四类数据 × 多模型评测

在 pilot_v2 的基础上，**按数据来源类型**抽样：真实数据、LLM 生成的有意义数据、LLM 生成的完全无意义(chaos)、LLM 生成的误导无意义(misleading)，每类**随机抽 10 条**，共 40 条，在多个多模态模型上跑同一套 QA，用于验证「数据来源 × 模型」的差异，并为全量实验提供小规模证据。

## 四类数据

| 类型 | 说明 | 来源 |
|------|------|------|
| **real** | 真实数据（GitHub 仓库中的 Mermaid 图） | `dataset/metadata.json`，目录 `000`–`499` |
| **meaningful** | LLM 生成的有意义流程图/架构图 | `dataset/synthetic_metadata.json`，`meaningful_*` |
| **chaos** | LLM 生成的完全混乱图（无常识可依） | `synthetic_metadata.json`，`nonsense_000`–`149`，`nonsense_subtype: chaos` |
| **misleading** | LLM 生成的误导图（真实概念+错误组合） | `synthetic_metadata.json`，`nonsense_150`–`299`，`nonsense_subtype: misleading` |

抽样种子固定为 `SEED=42`，保证可复现。

## 用法

```bash
# 项目根目录
python pilot_v3/run.py          # 全流程：抽样 → QA 生成 → 预检 → 评测
python pilot_v3/run.py qa      # 仅生成 QA（不覆盖已有）
python pilot_v3/run.py qa_regen # 重新生成 QA（覆盖）
python pilot_v3/run.py probe    # 仅预检模型
python pilot_v3/run.py eval     # 预检 + 评测
```

## 输出

- `pilot_v3/out/`：`real_00`–`09`、`meaningful_00`–`09`、`chaos_00`–`09`、`misleading_00`–`09`，每目录含 `diagram.mmd`、`description.txt`、`diagram.png`、`qa.json`
- `pilot_v3/out/manifest.json`：每目录的 `data_type` 与 `source_id`
- `pilot_v3/out/eval_results.jsonl`、`eval_results.json`：每条含 `data_type`、`model`、`correct`
- `pilot_v3/out/report.txt`：按数据来源、按模型、按模型×数据来源汇总
- `pilot_v3/ANALYSIS.md`：实验有效性、可得出结论、不足与改进方向

## 模型（与 pilot_v2 一致）

- qwen/qwen3-vl-30b-a3b-instruct
- qwen/qwen3-vl-30b-a3b-thinking
- qwen/qwen3-vl-8b-instruct
- qwen/qwen3-vl-8b-thinking
- qwen/qwen3-vl-235b-a22b-instruct
- qwen/qwen3-vl-235b-a22b-thinking

预检会过滤无法正常返回字母的模型。
