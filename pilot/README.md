# Pilot：风格化图片 + QA 小规模试跑

在**前 10 条**数据上跑通：多风格 PNG 生成 → QA 生成 → 多模型评测。**不读写 `dataset/`**，所有输出在 `pilot_data/`。

## 用法

```bash
# 项目根目录下
cd pilot
python run_pilot.py           # 全流程：准备样本 → 风格图 → QA → 评测
python run_pilot.py styles    # 仅生成多风格 PNG
python run_pilot.py qa        # 仅生成 QA
python run_pilot.py eval      # 仅跑评测（需已有 pilot_data/*/qa.json 与 diagram_*.png）
```

## 输出

- `pilot_data/000/` … `pilot_data/009/`：每目录含 `diagram.mmd`、`description.txt`（从 dataset 只读复制）、`diagram_default.png`、`diagram_dark.png`、`diagram_forest.png`、`diagram_neutral.png`、`qa.json`
- `pilot_data/eval_results.json`：每条 (sample, style, model, question) 的作答与对错
- `pilot_data/report.txt`：按模型、按风格、按模型×风格的准确率汇总
- `pilot_data/pilot.log`：运行日志

## 配置

- `PILOT_SIZE`、`STYLES`、`VISION_MODELS`、`QA_PER_SAMPLE` 在 `run_pilot.py` 顶部修改。
- OpenRouter API Key：环境变量 `OPENROUTER_API_KEY`，或从同仓库 `build_dataset.py` 中读取。

## 迭代策略

- **风格差异过小**：在 `run_pilot.py` 中调整 `STYLES`（如增加/更换 theme、bgColor），或换用 Kroki/本地 mmdc 等更差异化的渲染。
- **QA 全对/全错或模型间无差异**：调整 `run_pilot.py` 里 `generate_qa()` 的 prompt（难度混合、题型比例、选项数），或修改 `QA_PER_SAMPLE` 后重跑 `qa` 与 `eval`。
