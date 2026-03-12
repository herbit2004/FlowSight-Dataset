"""
Centralised constants, paths, and environment-variable accessors for FlowSight.
All values can be overridden via environment variables or .env.

Environment variable overrides (set before importing any flowsight module):
  FLOWSIGHT_BASE_DIR      — replaces DATASET_DIR  (e.g. "test_1" or absolute path)
  FLOWSIGHT_BENCHMARK_DIR — replaces BENCHMARK_DIR
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Project root & dataset directory ─────────────────────────────────────────
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

_custom_base = os.environ.get("FLOWSIGHT_BASE_DIR", "").strip()
if _custom_base:
    _base_path = Path(_custom_base)
    DATASET_DIR: Path = _base_path if _base_path.is_absolute() else PROJECT_ROOT / _base_path
else:
    DATASET_DIR = PROJECT_ROOT / "dataset"

# ── Progress / log files ─────────────────────────────────────────────────────
REAL_METADATA: Path = DATASET_DIR / "metadata.json"
SYNTH_METADATA: Path = DATASET_DIR / "synthetic_metadata.json"

CRAWL_PROGRESS: Path = DATASET_DIR / "crawl_progress.json"
DESCRIBE_PROGRESS: Path = DATASET_DIR / "describe_progress.json"
QA_PROGRESS: Path = DATASET_DIR / "qa_progress.json"
SYNTH_LOG: Path = DATASET_DIR / "synth.log"
CRAWL_LOG: Path = DATASET_DIR / "crawl.log"
DESCRIBE_LOG: Path = DATASET_DIR / "describe.log"
QA_LOG: Path = DATASET_DIR / "qa.log"

_custom_bench = os.environ.get("FLOWSIGHT_BENCHMARK_DIR", "").strip()
if _custom_bench:
    _bench_path = Path(_custom_bench)
    BENCHMARK_DIR: Path = _bench_path if _bench_path.is_absolute() else PROJECT_ROOT / _bench_path
elif _custom_base:
    # Sibling of the custom base dir, named <base>_benchmark
    BENCHMARK_DIR = DATASET_DIR.parent / (DATASET_DIR.name + "_benchmark")
else:
    BENCHMARK_DIR = PROJECT_ROOT / "benchmark_run"

# ── External API endpoints ────────────────────────────────────────────────────
OPENROUTER_URL: str = "https://openrouter.ai/api/v1/chat/completions"
MERMAID_INK: str = "https://mermaid.ink/img/{encoded}?type=png"

# ── Character / size limits ──────────────────────────────────────────────────
MAX_TREE_CHARS: int = 30_000
MAX_README_CHARS: int = 6_000
MAX_DOC_CHARS: int = 7_000
MAX_FILE_CHARS: int = 3_000
MAX_SELECTED_FILES: int = 6
MAX_MMD_CHARS: int = 6_000   # truncation for description prompts

# ── Crawl targets ────────────────────────────────────────────────────────────
TARGET_REAL: int = 500        # total real samples to collect
MAX_PER_REPO: int = 3

KNOWN_DOC_PATHS: list[str] = [
    "README.md", "ARCHITECTURE.md", "DESIGN.md", "OVERVIEW.md",
    "docs/README.md", "docs/architecture.md", "docs/design.md", "docs/overview.md",
    "doc/README.md", "doc/architecture.md", "documentation/README.md", "wiki/Home.md",
    ".github/README.md", "docs/getting-started.md", "docs/guide.md", "docs/workflow.md",
    "docs/flow.md", "docs/system-design.md", "docs/infrastructure.md", "docs/deployment.md",
]

PATH_BLACKLIST: tuple[str, ...] = (
    "/test", "/spec", "/example", "/sample", "/demo",
    "/fixture", "/mock", "/stub", "/playground",
)

REPO_QUERIES: list[str] = [
    '"graph TD" mermaid in:readme', '"graph LR" mermaid in:readme',
    '"flowchart TD" in:readme', '"flowchart LR" in:readme', '"graph TB" mermaid in:readme',
    'mermaid architecture in:readme microservices', 'mermaid diagram in:readme kubernetes',
    'mermaid flowchart in:readme CI/CD', 'mermaid graph in:readme "system design"',
    'mermaid architecture in:readme backend', 'mermaid diagram in:readme cloud',
    'mermaid graph in:readme "API gateway"', 'mermaid flow in:readme deployment',
    'mermaid diagram in:readme database', 'mermaid graph in:readme authentication',
    'mermaid diagram in:readme pipeline', 'mermaid architecture in:readme docker',
    'mermaid graph in:readme workflow', 'mermaid diagram in:readme "event driven"',
    'mermaid architecture in:readme infrastructure', 'mermaid flowchart in:readme serverless',
    'mermaid graph in:readme "data flow"', 'mermaid diagram in:readme monitoring',
    'mermaid graph in:readme "load balancer"', 'mermaid diagram in:readme "message queue"',
    'mermaid flowchart in:readme "state machine"', 'mermaid graph in:readme "distributed system"',
    'mermaid diagram in:readme "monitoring"', 'mermaid architecture in:readme "security"',
    'mermaid graph in:readme "caching"', 'mermaid flowchart in:readme "onboarding"',
    'mermaid diagram in:readme "testing"', 'mermaid graph in:readme "logging"',
    'mermaid architecture in:readme "scalability"', 'mermaid diagram in:readme "messaging"',
    'mermaid graph in:readme "sync"', 'mermaid flowchart in:readme "approval"',
    'mermaid diagram in:readme "migration"', 'mermaid graph in:readme "gateway"',
    'mermaid architecture in:readme "multi-tenant"', 'mermaid diagram in:readme "batch"',
    'mermaid graph in:readme "real-time"',
]

# ── Synthetic data targets ────────────────────────────────────────────────────
SYNTH_MEANINGFUL: int = 200   # meaningful_000 – meaningful_199
SYNTH_CHAOS: int = 150        # nonsense_000   – nonsense_149
SYNTH_MISLEADING: int = 150   # nonsense_150   – nonsense_299

# Meaningful diagram themes (rotated by local index to ensure diversity)
MEANINGFUL_THEMES: list[str] = [
    "user registration and login flow",
    "order creation and payment processing",
    "product search and recommendation pipeline",
    "inventory deduction and rollback",
    "message queue producer-consumer flow",
    "cache read/write and invalidation",
    "API gateway routing and authentication",
    "microservice RPC call chain",
    "log collection and aggregation",
    "metrics reporting and alerting",
    "configuration center push/pull",
    "distributed lock and leader election",
    "file upload and object storage",
    "data synchronization and ETL pipeline",
    "approval workflow",
    "permission and role validation",
    "session management and single sign-on",
    "payment callback and reconciliation",
    "risk-control rule engine",
    "recommendation ranking pipeline",
    "search index update flow",
    "scheduled job dispatch",
    "retry and circuit-breaker logic",
    "canary release and traffic switching",
    "database read/write splitting",
    "sharding and routing",
    "transaction and compensation (saga)",
    "event sourcing",
    "device telemetry reporting and command dispatch",
    "real-time stream processing with windowing",
    "batch job DAG",
    "data lake tiering",
    "customer support ticket routing",
    "marketing campaign rule engine",
    "coupon issuance and redemption",
    "loyalty points and tier management",
    "push notification strategy",
    "event tracking and behavioral analytics",
    "A/B experiment traffic splitting",
    "feature engineering pipeline",
    "model training and deployment flow",
    "inference service call chain",
    "knowledge graph construction",
    "full-text search and highlighting",
    "multi-tenant isolation",
    "quota and rate limiting",
    "audit logging",
    "data masking and encryption",
    "container orchestration and auto-scaling",
    "service discovery and health checks",
    "gateway rate limiting and circuit breaking",
    "distributed tracing",
    "report generation and export",
    "real-time dashboard data pipeline",
    "SLA tracking and ticket escalation",
    "resource request and approval",
    "container image build and release",
    "config change and rollback",
    "secret rotation",
    "backup and restore",
    "cross-region data sync",
    "multi-active failover",
    "hot/cold data tiering",
    "archival and cleanup policy",
    "device heartbeat and offline detection",
    "firmware OTA update flow",
    "rule matching and action execution",
    "workflow state machine",
    "multi-step form validation and submission",
    "comment, like, and feed pipeline",
    "live-stream push/pull",
    "video transcoding and screenshot",
    "CDN origin fetch",
    "watermark and authorization",
    "invoice request and issuance",
    "contract signing flow",
    "reconciliation and settlement",
    "bill generation",
    "customer service bot dialogue",
    "ticket auto-assignment",
    "knowledge base retrieval",
    "QA sampling and review",
    "warehouse inbound and outbound",
    "shipment tracking and delivery",
    "return and exchange flow",
    "after-sales compensation",
    "membership tier and benefits",
    "daily check-in and task completion",
    "referral and viral growth",
    "points redemption",
    "security scan and vulnerability patching",
    "dependency analysis and license check",
    "code review and merge flow",
    "environment and release gate",
]

# ── QA settings ──────────────────────────────────────────────────────────────
QA_PER_SAMPLE: int = 6
QA_MODEL_DEFAULT: str = "google/gemini-2.0-flash-001"

# ── Benchmark defaults ────────────────────────────────────────────────────────
DEFAULT_BENCHMARK_MODELS: list[str] = [
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

DEFAULT_BENCHMARK_COUNTS: dict[str, int] = {
    "real": 250,
    "meaningful": 100,
    "chaos": 75,
    "misleading": 75,
}


def get_generation_model() -> str:
    """Return the model used for crawl/synth/describe/qa generation steps."""
    from env_config import load_env
    load_env()
    return os.environ.get("GENERATION_MODEL", QA_MODEL_DEFAULT).strip()


def get_benchmark_models() -> list[str]:
    """Return the list of models to use in benchmark evaluation (from .env)."""
    from env_config import load_env
    load_env()
    raw = os.environ.get("BENCHMARK_MODELS", "").strip()
    if raw:
        return [m.strip() for m in raw.split(",") if m.strip()]
    return list(DEFAULT_BENCHMARK_MODELS)
