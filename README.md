# FlowSight 数据集（FlowSight-Dataset）

FlowSight 是一个面向**多模态流程图/架构图理解与生成**的评测数据集。每条样本由 Mermaid 源码、渲染图像与结构化中文描述组成，适用于图表理解、描述生成、图文对齐等任务的模型评估（不用于微调）。

---

## 数据集概览

### 样本结构

每个样本对应 `dataset/<id>/` 目录，包含：

| 文件 | 说明 |
|------|------|
| `diagram.mmd` | Mermaid 源码（graph / flowchart 等） |
| `diagram.png` | 由 [mermaid.ink](https://mermaid.ink) 渲染的 PNG 图 |
| `description.txt` | 结构化中文描述（见下） |

元数据统一存放在 `dataset/metadata.json`（JSON 数组），每项包含：`id`、`repo`、`repo_stars`、`file_path`、`branch`、`raw_url`、`mermaid_hash`、`struct_hash`、`ai_reason`、`files` 等字段。

### 描述格式（description.txt）

描述采用固定的 **7 节**结构，便于作为评测与 QA 的 ground truth：

1. **图类型与用途** — 图的类型、描述对象、在仓库中的作用  
2. **图的整体布局** — 方向（TD/LR/TB）、层次、起点/终点  
3. **分组/子图/阶段说明** — subgraph / 阶段划分  
4. **节点逐项说明** — 关键节点及仓库语境下的含义  
5. **连线、分支与汇聚关系** — 边与条件分支的说明  
6. **仓库语境与术语解释** — 与图相关的术语、模块、配置  
7. **可作为 QA Ground Truth 的高信息密度摘要** — 一段可还原主结构的摘要  

### 质量与来源

- **来源**：GitHub 热门仓库的 README 及文档（按 stars 排序），覆盖微服务、云原生、CI/CD、系统设计、API、数据流等场景。  
- **过滤**：多语言 README 过滤（仅保留英文主 README）、规则预过滤（节点数、标签质量、路径黑名单）、AI 质量判断（Gemini Flash 判定是否为真实架构/流程图）。  
- **去重**：按节点 ID 与连线拓扑做结构去重，跨仓库与同仓库内去重；每仓库最多保留若干张不重复结构的图。

---

## 当前构建流程

构建由单脚本 `build_dataset.py` 完成，从爬取到生成 description 一气呵成。

### 流程步骤

1. **爬取** — 按预设搜索词在 GitHub 搜索仓库，从已知文档路径（如 README.md、docs/architecture.md）拉取内容，通过 raw CDN 下载，尽量少用 REST API。  
2. **过滤与去重** — 提取 Mermaid 块，经规则过滤与 AI 质量判断，再按结构 hash 去重。  
3. **落盘与渲染** — 通过 mermaid.ink 将 Mermaid 渲染为 PNG，与源码一并写入样本目录。  
4. **上下文拉取** — 拉取仓库目录树、README、图所在文档；由 LLM 从仓库中选取与图最相关的代码/配置文件并下载片段。  
5. **多模态生成描述** — 将 PNG、Mermaid、README、文档上下文、所选代码片段一并送入多模态模型（OpenRouter / Gemini），生成上述 7 节结构化 description，写入 `description.txt`。  
6. **写元数据** — 仅当 mmd、png、description 均成功时，才将该样本目录计入并追加到 `metadata.json`，避免出现孤儿目录或残缺样本。

### 运行方式

```bash
# 在 FlowSight-Dataset 目录下
pip install requests
python build_dataset.py
```

- **首次运行**：从零采集，目标条数由脚本内 `TARGET_COUNT` 控制（默认 100）。  
- **续采**：若已存在 `dataset/metadata.json`，则在其基础上继续采集；目标条数 = 当前条数 + 环境变量 `ADD_MORE`（默认 100），例如：  
  `ADD_MORE=200 python build_dataset.py`  
- **可选**：设置环境变量 `GITHUB_TOKEN` 可提高 GitHub API 限额；OpenRouter API Key 需在脚本内配置。

构建日志写入 `dataset/build.log`。

---

## 后续构建计划

- **QA 对生成**：基于现有 description 与图表，生成问答对并纳入样本（如四元组：image, mermaid, description, QA）。  
- **多风格图像**：对同一 Mermaid 源码生成多种渲染风格（如不同 Mermaid 主题），用于风格鲁棒性或多模态对齐实验。  
- **合成数据扩展**：在真实采集样本之外，增加合成 Mermaid 图（例如：一部分为“拟真”架构/流程图，一部分为“反事实/无意义”图），用于区分能力与鲁棒性评测。  
- **规模与多样性**：继续扩展采集关键词与仓库来源，提高样本数量与领域覆盖。

---

## 目录结构

```
FlowSight-Dataset/
├── README.md           # 本文件
├── build_dataset.py    # 数据集构建脚本
├── dataset/
│   ├── metadata.json   # 样本元数据（JSON 数组）
│   ├── README.md       # 数据集简要说明
│   ├── build.log       # 构建日志
│   ├── 000/
│   │   ├── diagram.mmd
│   │   ├── diagram.png
│   │   └── description.txt
│   ├── 001/
│   └── ...
└── OpenRouterDocs-main/   # （可选）OpenRouter API 参考
```
