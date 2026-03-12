# FlowSight Dataset

FlowSight is a **multimodal flowchart/architecture diagram understanding** benchmark dataset.
Each sample consists of a Mermaid source file, a rendered PNG image, a structured English
description, and multiple-choice QA — designed for evaluating multimodal model capabilities
across tasks such as diagram comprehension, description generation, and image-text alignment.

---

## Dataset Overview

### Sample types

| Type | Directory pattern | Count | Notes |
|------|-------------------|-------|-------|
| **Real** | `dataset/000` – `dataset/499` | 500 | Crawled from GitHub real-world repositories |
| **Meaningful** | `dataset/meaningful_000` – `…_199` | 200 | Synthetic — realistic fictional flows |
| **Chaos** | `dataset/nonsense_000` – `…_149` | 150 | Synthetic — deliberately incoherent |
| **Misleading** | `dataset/nonsense_150` – `…_299` | 150 | Synthetic — counterfactual errors injected |

### Files per sample

| File | Description |
|------|-------------|
| `diagram.mmd` | Mermaid source (graph / flowchart syntax) |
| `diagram.png` | PNG rendered by [mermaid.ink](https://mermaid.ink) |
| `context.json` | *(real samples only)* Repository context: tree, README, doc excerpt, code snippets |
| `description.txt` | 7-section structured English description |
| `qa.json` | 6 multiple-choice questions (JSON array) |

Metadata files:
- `dataset/metadata.json` — real samples
- `dataset/synthetic_metadata.json` — synthetic samples

### Description format (7 sections)

1. **Diagram Type & Purpose** — type, subject, role in the repository
2. **Overall Layout** — direction (TD/LR/TB), hierarchy, start/end nodes
3. **Subgraphs / Stages** — explicit subgraphs or logical stage divisions
4. **Node-by-Node Description** — every key node with repository context where available
5. **Edges, Branches & Convergence** — edge descriptions and branch conditions
6. **Repository Context & Terminology** — terms, modules, configs relevant to the diagram
7. **High-Density QA Ground Truth Summary** — self-contained dense paragraph for QA reference

### QA format

Each `qa.json` contains 6 items:

```json
[
  {
    "question": "Which node is reached when branch condition is No?",
    "options": ["A. NodeX", "B. NodeY", "C. NodeZ", "D. NodeW"],
    "correct_index": 1,
    "type": "reasoning",
    "difficulty": "medium"
  }
]
```

Question type distribution per sample: ≥2 reasoning, ≥1 negation; difficulty: ≤1 easy, ≥2 medium, ≥2 hard.

---

## Quick Start

```bash
cp .env.example .env        # fill in OPENROUTER_API_KEY (and optionally GITHUB_TOKEN)
uv sync                     # install dependencies into .venv
```

### Step-by-step dataset generation

```bash
# 1. Crawl 500 real diagrams from GitHub (resumable)
uv run python main.py crawl

# 2. Generate 500 synthetic diagrams (resumable)
uv run python main.py synth

# 3. Generate descriptions for all samples (resumable)
uv run python main.py describe

# 4. Generate QA for all samples (resumable)
uv run python main.py qa

# 5. Run multi-model benchmark evaluation
uv run python main.py benchmark init
uv run python main.py benchmark run
```

All steps are **interruptible and resumable** — re-run the same command to continue from
where it left off.

### CLI reference

```
python main.py crawl      [--target N] [--add-more N]
python main.py synth      [--type meaningful|chaos|misleading|all] [--count N] [--start-index N]
python main.py describe   [--type real|meaningful|chaos|misleading|all] [--overwrite] [--retry-failed]
python main.py qa         [--type real|meaningful|chaos|misleading|all] [--overwrite] [--retry-failed]
python main.py benchmark  [init|run|status|retry-failed] [--allow-partial]
                          [--count-real N] [--count-meaningful N] [--count-chaos N] [--count-misleading N]
```

---

## Environment variables (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | **Yes** | Used for all LLM calls |
| `GITHUB_TOKEN` | No | Increases GitHub API rate limit (5000 vs 60 req/hr) |
| `GENERATION_MODEL` | No | LLM for crawl/synth/describe/qa (default: `google/gemini-2.0-flash-001`) |
| `BENCHMARK_MODELS` | No | Comma-separated model IDs for benchmark evaluation |

See `.env.example` for full details and default values.

---

## Project structure

```
FlowSight-Dataset/
├── main.py                  # Unified CLI entry point
├── env_config.py            # API key & model config loader
├── .env.example             # Template — copy to .env and fill in keys
├── pyproject.toml           # uv / pip dependency file
├── flowsight/
│   ├── __init__.py
│   ├── config.py            # Constants, paths, targets, themes
│   ├── utils.py             # Shared: logging, HTTP, OpenRouter API, mermaid.ink, helpers
│   ├── crawl.py             # GitHub crawl module
│   ├── synth.py             # Synthetic diagram generation module
│   ├── describe.py          # Description generation module
│   ├── qa.py                # QA generation module
│   └── benchmark.py         # Benchmark evaluation module
└── dataset/
    ├── metadata.json
    ├── synthetic_metadata.json
    ├── 000/ … 499/          (real: mmd + png + context + description + qa)
    ├── meaningful_000/ …    (synthetic meaningful)
    └── nonsense_000/ …      (synthetic chaos / misleading)
```

---

## Quality & sourcing

- **Source**: GitHub top-starred repositories (sorted by stars), across domains including
  microservices, cloud-native, CI/CD, system design, API gateways, data pipelines, etc.
- **Filtering**: English-only README filter; rule-based pre-filter (node count, label quality,
  path blacklist); AI quality check (LLM judges whether diagram has genuine architectural /
  process value, not tutorial or placeholder content).
- **Deduplication**: Structural hash deduplication by node/edge topology — across repositories
  and within the same repository; maximum `MAX_PER_REPO` (3) non-duplicate diagrams per repo.
