# Pilot V2：前 10 条 × 默认风格 × 分类型分难度 QA × 5 个 Qwen 模型

独立于 `pilot/`，用前 10 条数据、**仅默认风格图**（`diagram.png`）、**分类型分难度**的 QA，在 5 个 Qwen 模型上做预检 + **并行评测**，用于验证 QA 设计和模拟最终实验。

## 模型

- qwen/qwen3-vl-30b-a3b-instruct
- qwen/qwen3-vl-30b-a3b-thinking
- qwen/qwen3-vl-8b-instruct
- qwen/qwen3-vl-8b-thinking
- qwen/qwen3-vl-235b-a22b-instruct
- qwen/qwen3-vl-235b-a22b-thinking

（预检会过滤掉无法正常返回字母的模型，如非视觉模型。）

## 用法

```bash
# 项目根目录
python pilot_v2/run.py          # 全流程：样本 → QA → 预检 → 评测
python pilot_v2/run.py probe    # 仅预检
python pilot_v2/run.py qa       # 仅生成 QA
python pilot_v2/run.py eval     # 预检 + 评测（并行多模型）
```

## 输出

- `pilot_v2/out/000/` … `009/`：`diagram.mmd`、`description.txt`、`diagram.png`、`qa.json`（含 `type`、`difficulty`）
- `pilot_v2/out/probe_ok.json`：预检通过/未通过模型
- `pilot_v2/out/eval_results.jsonl`、`eval_results.json`：每条含 type、difficulty
- `pilot_v2/out/report.txt`：按模型、按类型、按难度、按模型×类型、按模型×难度汇总
- `pilot_v2/out/pilot_v2.log`：日志

## QA 设计

- 每道题标注 **type**：`factual` / `reasoning` / `negation`
- 每道题标注 **difficulty**：`easy` / `medium` / `hard`
- 生成时要求类型与难度覆盖、且能在不同参数量/类型模型上产生差异。
