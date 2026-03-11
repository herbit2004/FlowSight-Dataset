# run_benchmark.py 使用说明

FlowSight 全量评测脚本：在分层抽样的 500 条数据上，用 10 个多模态模型跑「每张图一次性答完所有 QA」的评测，支持断点续跑、暂停恢复与失败重试。

---

## 一、做什么

- **数据**：从 `dataset/` 按类型分层随机抽 500 条（默认 real=250, meaningful=100, chaos=75, misleading=75），需具备 `diagram.png` 和 `qa.json`。
- **协议**：每张图发一次请求，把该图下所有题目一起问，模型返回一个答案数组（JSON），与标准答案逐题比对。
- **模型**：脚本内写死的 10 个 OpenRouter 多模态模型（Qwen3-VL 6 个 + 闭源 4 个），单线程串行、任务顺序随机。
- **可恢复**：每次 `run` 前会做模型预检；支持 Ctrl+C / 暂停标记安全退出，下次 `run` 从未完成任务继续；`retry_failed` 可把失败任务重新跑。

---

## 二、环境与依赖

- Python 3，需安装 `requests`。
- **API Key**：设置环境变量 `OPENROUTER_API_KEY`，或在项目根目录的 `build_dataset.py` 里写 key（脚本会尝试读取）。
- **数据集**：`dataset/metadata.json`（真实样本 id）、`dataset/synthetic_metadata.json`（meaningful / chaos / misleading），且每个样本目录下有 `diagram.png` 和 `qa.json`。

---

## 三、命令

在项目根目录执行。

| 命令 | 说明 |
|------|------|
| `python run_benchmark.py init` | 按分层配额随机抽 500 条，生成任务列表并初始化输出目录；已有 state 时需加 `--force` 才会覆盖。 |
| `python run_benchmark.py run` | 先预检全部模型，再执行/继续执行评测（跳过已 `done` 的任务）。 |
| `python run_benchmark.py status` | 查看当前进度（done/pending/failed）和累计统计（JSON 打印到终端）。 |
| `python run_benchmark.py pause` | 写入暂停标记；正在运行的 `run` 会在下一个任务结束后安全退出。 |
| `python run_benchmark.py resume` | 删除暂停标记，之后可再次 `run` 继续。 |
| `python run_benchmark.py retry_failed` | 将所有 `failed` 任务重置为 `pending`，下次 `run` 会重新尝试。 |

**常用流程：**

```bash
python run_benchmark.py init
python run_benchmark.py run
# 若需暂停：另开终端执行 python run_benchmark.py pause，或直接 Ctrl+C
python run_benchmark.py resume   # 仅当用过 pause 时
python run_benchmark.py run      # 继续
python run_benchmark.py status   # 查看进度与统计
```

---

## 四、init 可选参数

- `--out-dir PATH`：输出目录，默认 `benchmark_run`。
- `--seed N`：随机种子，默认 42。
- `--total N`：总样本数，默认 500，需与 `--counts` 各类型数量之和一致。
- `--counts "real=250,meaningful=100,chaos=75,misleading=75"`：各类型抽样数量。
- `--force`：若已存在 `state.json`，加此参数才会重新 init 并覆盖。

---

## 五、run 可选参数

- `--max-attempts N`：每个任务最多请求重试次数，默认 3。
- `--sleep-between SEC`：任务之间休眠秒数，默认 0.2。
- `--log-every N`：每处理 N 个任务输出一次阶段性统计（进度、按数据来源、按模型、按模型×来源），默认 20。
- `--allow-partial`：预检时若有模型失败，仍对通过预检的模型继续跑（未通过模型对应任务保持 pending）。

---

## 六、输出目录（默认 benchmark_run/）

| 文件 | 说明 |
|------|------|
| `state.json` | 任务状态与抽样信息，断点续跑依赖此文件。 |
| `selection_manifest.json` | 本次抽中的 500 条样本列表（含 data_type、path 等）。 |
| `results.jsonl` | 每条一题一行：sample_id, data_type, model, qidx, correct_letter, predicted, correct 等。 |
| `responses.jsonl` | 每次「一图多题」调用的原始回答摘要（sample_id, model, answers, raw_text 等）。 |
| `run.log` | 时间戳日志：预检结果、进度、阶段性统计（按数据来源、按模型、按模型×数据来源）。 |
| `probe_history.jsonl` | 每次 run 的模型预检记录。 |
| `PAUSE.flag` | 存在时表示已请求暂停，run 会在下一任务后退出。 |

---

## 七、当前模型列表（脚本内 MODELS）

- Qwen3-VL：`qwen/qwen3-vl-8b-instruct`、`qwen/qwen3-vl-30b-a3b-instruct`、`qwen/qwen3-vl-235b-a22b-instruct`、`qwen/qwen3-vl-8b-thinking`、`qwen/qwen3-vl-30b-a3b-thinking`、`qwen/qwen3-vl-235b-a22b-thinking`
- 闭源：`google/gemini-2.5-flash-lite`、`google/gemini-2.5-flash`、`bytedance-seed/seed-2.0-mini`、`openai/gpt-4o-mini`

修改模型需直接编辑 `run_benchmark.py` 中的 `MODELS` 列表。若已 init 过，换模型后**不会**自动变更已有 state 中的任务集合，只影响之后新 init 的 run（建议换模型后重新 `init --force` 再 `run`）。

---

## 八、注意

- **预检**：每次 `run` 都会先对全部模型发一次简单请求（单图+单题），默认任一失败即不进入正式评测；可用 `--allow-partial` 放宽。
- **中断**：Ctrl+C 或 kill 会触发安全退出，当前任务完成后保存 state 再退出；下次 `run` 从中断处继续。
- **网络**：单次请求 timeout 较长（约 150 秒），若长时间无新日志，可能是某次请求卡住，可 Ctrl+C 后重新 `run`（未完成任务会保留为 pending 或 running，running 会在下次被当作 pending 再跑）。

更多实验设计与模型选型说明见 `docs/experiment_plan_1000.md` 第六节。
