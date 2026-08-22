from __future__ import annotations

import argparse
from pathlib import Path

from app.benchmarks.datasets import REQUIRED_WORKLOADS
from app.benchmarks.harness import BenchmarkConfig, load_report, run_benchmarks, write_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic Greenmile Round 2 benchmarks")
    parser.add_argument("--sizes", default=",".join(map(str, REQUIRED_WORKLOADS)))
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20_260_823)
    parser.add_argument("--strategies", default="baseline-v1", help="Comma-separated strategies: baseline-v1,optimized-v2")
    parser.add_argument("--compare-baseline", type=Path, default=None, help="Existing baseline-v1 JSON report to compare against without overwriting it")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/round2-baseline.json"))
    arguments = parser.parse_args()
    config = BenchmarkConfig(
        workloads=tuple(int(value.strip()) for value in arguments.sizes.split(",") if value.strip()),
        warmups=arguments.warmups,
        repetitions=arguments.runs,
        seed=arguments.seed,
        strategies=tuple(value.strip() for value in arguments.strategies.split(",") if value.strip()),
    )
    baseline = load_report(arguments.compare_baseline)
    json_path, markdown_path = write_report(run_benchmarks(config, compare_baseline=baseline), arguments.output)
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")


if __name__ == "__main__":
    main()
