#!/usr/bin/env python3
"""
FlowSight Dataset Toolkit — unified CLI entry point.

Sub-commands
------------
  crawl      Crawl GitHub for real Mermaid diagrams (resumable)
  synth      Generate synthetic Mermaid diagrams (resumable)
  describe   Generate 7-section descriptions for all samples (resumable)
  qa         Generate multiple-choice QA for all samples (resumable)
  benchmark  Run multi-model evaluation (init / run / status / retry-failed)

Quick start
-----------
  cp .env.example .env          # fill in OPENROUTER_API_KEY
  uv sync                       # install dependencies
  uv run python main.py crawl
  uv run python main.py synth
  uv run python main.py describe
  uv run python main.py qa
  uv run python main.py benchmark init
  uv run python main.py benchmark run --workers 10

All commands are safe to interrupt (Ctrl-C) and resume.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _set_base_dir(base_dir: str | None) -> None:
    """Set FLOWSIGHT_BASE_DIR / FLOWSIGHT_BENCHMARK_DIR env vars before any flowsight import."""
    if not base_dir:
        return
    p = Path(base_dir)
    if not p.is_absolute():
        p = Path.cwd() / p
    os.environ["FLOWSIGHT_BASE_DIR"] = str(p)
    os.environ["FLOWSIGHT_BENCHMARK_DIR"] = str(p.parent / (p.name + "_benchmark"))


def _crawl(args: argparse.Namespace) -> None:
    from flowsight import crawl
    crawl.run(target=args.target, add_more=args.add_more)


def _synth(args: argparse.Namespace) -> None:
    from flowsight import synth
    synth.run(
        synth_type=args.type,
        count=args.count,
        start_index=args.start_index,
        workers=args.workers,
    )


def _describe(args: argparse.Namespace) -> None:
    from flowsight import describe
    describe.run(
        describe_type=args.type,
        overwrite=args.overwrite,
        retry_failed=args.retry_failed,
        workers=args.workers,
    )


def _qa(args: argparse.Namespace) -> None:
    from flowsight import qa
    qa.run(
        qa_type=args.type,
        overwrite=args.overwrite,
        retry_failed=args.retry_failed,
        workers=args.workers,
    )


def _benchmark(args: argparse.Namespace) -> None:
    from flowsight import benchmark

    counts: dict[str, int] | None = None
    if any([args.count_real, args.count_meaningful, args.count_chaos, args.count_misleading]):
        from flowsight.config import DEFAULT_BENCHMARK_COUNTS
        counts = dict(DEFAULT_BENCHMARK_COUNTS)
        if args.count_real is not None:
            counts["real"] = args.count_real
        if args.count_meaningful is not None:
            counts["meaningful"] = args.count_meaningful
        if args.count_chaos is not None:
            counts["chaos"] = args.count_chaos
        if args.count_misleading is not None:
            counts["misleading"] = args.count_misleading

    benchmark.run(
        sub=args.sub,
        counts=counts,
        workers=args.workers,
        qa_mode=args.qa_mode,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="FlowSight Dataset Toolkit",
    )
    parser.add_argument(
        "--base-dir", default=None, dest="base_dir", metavar="DIR",
        help="Override dataset directory (default: dataset/). "
             "Benchmark state will be stored in <DIR>_benchmark/. "
             "Example: --base-dir test_1",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── crawl ──────────────────────────────────────────────────────────────
    p_crawl = sub.add_parser("crawl", help="Crawl GitHub for real Mermaid diagrams")
    p_crawl.add_argument("--target", type=int, default=None)
    p_crawl.add_argument("--add-more", type=int, default=None, dest="add_more")
    p_crawl.set_defaults(func=_crawl)

    # ── synth ──────────────────────────────────────────────────────────────
    p_synth = sub.add_parser("synth", help="Generate synthetic Mermaid diagrams")
    p_synth.add_argument("--type", choices=["meaningful", "chaos", "misleading", "all"],
                         default="all")
    p_synth.add_argument("--count", type=int, default=None)
    p_synth.add_argument("--start-index", type=int, default=0, dest="start_index")
    p_synth.add_argument("--workers", type=int, default=25, metavar="N",
                         help="Parallel threads (default: 25)")
    p_synth.set_defaults(func=_synth)

    # ── describe ───────────────────────────────────────────────────────────
    p_desc = sub.add_parser("describe", help="Generate 7-section descriptions")
    p_desc.add_argument("--type", choices=["real", "meaningful", "chaos", "misleading", "all"],
                        default="all")
    p_desc.add_argument("--overwrite", action="store_true")
    p_desc.add_argument("--retry-failed", action="store_true", dest="retry_failed")
    p_desc.add_argument("--workers", type=int, default=25, metavar="N")
    p_desc.set_defaults(func=_describe)

    # ── qa ─────────────────────────────────────────────────────────────────
    p_qa = sub.add_parser("qa", help="Generate multiple-choice QA")
    p_qa.add_argument("--type", choices=["real", "meaningful", "chaos", "misleading", "all"],
                      default="all")
    p_qa.add_argument("--overwrite", action="store_true")
    p_qa.add_argument("--retry-failed", action="store_true", dest="retry_failed")
    p_qa.add_argument("--workers", type=int, default=25, metavar="N")
    p_qa.set_defaults(func=_qa)

    # ── benchmark ──────────────────────────────────────────────────────────
    p_bench = sub.add_parser("benchmark", help="Multi-model evaluation")
    p_bench.add_argument("sub", nargs="?", default="run",
                         choices=["init", "run", "status", "retry-failed"])
    p_bench.add_argument("--workers", type=int, default=25, metavar="N",
                         help="Parallel threads for benchmark run (default: 25)")
    p_bench.add_argument("--qa-mode", choices=["batch", "single"], default="batch",
                         dest="qa_mode",
                         help="batch: all QA in one call (default); "
                              "single: one QA per API call with image")
    p_bench.add_argument("--count-real", type=int, default=None, dest="count_real")
    p_bench.add_argument("--count-meaningful", type=int, default=None, dest="count_meaningful")
    p_bench.add_argument("--count-chaos", type=int, default=None, dest="count_chaos")
    p_bench.add_argument("--count-misleading", type=int, default=None, dest="count_misleading")
    p_bench.set_defaults(func=_benchmark)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _set_base_dir(args.base_dir)
    args.func(args)


if __name__ == "__main__":
    main()
