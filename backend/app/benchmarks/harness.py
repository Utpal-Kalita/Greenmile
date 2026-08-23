from __future__ import annotations

import gc
import importlib
import json
import platform
import resource
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter, process_time
from typing import Any, Protocol

import psutil

from app.benchmarks.baseline import BASELINE_VERSION, run_baseline_v1
from app.benchmarks.datasets import REQUIRED_WORKLOADS, BenchmarkScenario, generate_scenario
from app.benchmarks.timing import STAGES
from app.benchmarks.validation import validate_benchmark_route
from app.core.config import Settings
from app.optimizer.engine import HaversineProvider, MetricsEngine, RouteOptimizer

OPTIMIZED_VERSION = "optimized-v2"


class StrategyResult(Protocol):
    plan: Any
    timings: dict[str, float]


StrategyRunner = Callable[[RouteOptimizer, Sequence[Any], Sequence[Any], Any], StrategyResult]


@dataclass(frozen=True)
class BenchmarkConfig:
    workloads: tuple[int, ...] = REQUIRED_WORKLOADS
    warmups: int = 2
    repetitions: int = 10
    seed: int = 20_260_823
    strategies: tuple[str, ...] = (BASELINE_VERSION,)

    def __post_init__(self) -> None:
        if not self.workloads or any(item not in REQUIRED_WORKLOADS for item in self.workloads):
            raise ValueError(f"workloads must contain only {REQUIRED_WORKLOADS}")
        if self.warmups < 0 or self.repetitions < 1:
            raise ValueError("warmups must be non-negative and repetitions positive")
        allowed = {BASELINE_VERSION, OPTIMIZED_VERSION}
        if not self.strategies or any(strategy not in allowed for strategy in self.strategies):
            raise ValueError(f"strategies must contain only {sorted(allowed)}")


def nearest_rank(samples: Sequence[float], percentile: float) -> float:
    if not samples:
        raise ValueError("samples are required")
    ordered = sorted(samples)
    rank = max(1, min(len(ordered), __import__("math").ceil(percentile / 100 * len(ordered))))
    return round(ordered[rank - 1], 3)


def run_benchmarks(
    config: BenchmarkConfig,
    settings: Settings | None = None,
    *,
    compare_baseline: Mapping[str, Any] | None = None,
    strategy_runners: Mapping[str, StrategyRunner] | None = None,
) -> dict[str, Any]:
    settings = settings or Settings()
    runners = _strategy_runners(strategy_runners)
    process = psutil.Process()
    workloads = []
    legacy_baseline_only = config.strategies == (BASELINE_VERSION,) and compare_baseline is None

    for stop_count in config.workloads:
        scenario = generate_scenario(stop_count, seed=config.seed)
        if legacy_baseline_only:
            workloads.append(_legacy_workload(_run_strategy(BASELINE_VERSION, runners[BASELINE_VERSION], scenario, settings, process, warmups=config.warmups, repetitions=config.repetitions), scenario))
            continue

        workload: dict[str, Any] = {
            "dataset": scenario.name,
            "dataset_version": scenario.version,
            "seed": scenario.seed,
            "stop_count": stop_count,
            "vehicle_count": len(scenario.vehicles),
            "strategies": {},
        }
        baseline_workload = _baseline_workload(compare_baseline, stop_count)
        strategies = config.strategies
        if compare_baseline is not None and OPTIMIZED_VERSION in strategies and BASELINE_VERSION not in strategies:
            strategies = (BASELINE_VERSION, *strategies)
        for strategy in strategies:
            if strategy == BASELINE_VERSION and baseline_workload is not None:
                workload["strategies"][strategy] = baseline_workload
                continue
            workload["strategies"][strategy] = _run_strategy(strategy, runners[strategy], scenario, settings, process, warmups=config.warmups, repetitions=config.repetitions)
        if BASELINE_VERSION in workload["strategies"] and OPTIMIZED_VERSION in workload["strategies"]:
            workload["comparison"] = _comparison(workload["strategies"][BASELINE_VERSION], workload["strategies"][OPTIMIZED_VERSION])
        workloads.append(workload)

    return {
        "schema_version": "greenmile-round2-benchmark-v1" if legacy_baseline_only else "greenmile-round2-benchmark-v2",
        "generated_at": datetime.now(UTC).isoformat(),
        "git_sha": _git_sha(),
        "environment": _environment(),
        "config": asdict(config),
        "algorithm_changed": False if legacy_baseline_only else None,
        "baseline_preserved": not legacy_baseline_only,
        "workloads": workloads,
    }


def write_report(report: dict[str, Any], output: Path) -> tuple[Path, Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    markdown = output.with_suffix(".md")
    markdown.write_text(_markdown(report) + "\n")
    return output, markdown


def load_report(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text())


def _run_strategy(
    strategy: str,
    runner: StrategyRunner,
    scenario: BenchmarkScenario,
    settings: Settings,
    process: psutil.Process,
    *,
    warmups: int,
    repetitions: int,
) -> dict[str, Any]:
    optimizer = RouteOptimizer(HaversineProvider(), settings)
    for _ in range(warmups):
        runner(optimizer, scenario.stops, scenario.vehicles, scenario.depot)
    samples = []
    for repetition in range(repetitions):
        gc.collect()
        rss_before = process.memory_info().rss
        cpu_before = process_time()
        wall_before = perf_counter()
        result = runner(optimizer, scenario.stops, scenario.vehicles, scenario.depot)
        wall_ms = (perf_counter() - wall_before) * 1_000
        cpu_ms = (process_time() - cpu_before) * 1_000
        rss_after = process.memory_info().rss
        with _measure(result.timings, "metrics_ms"):
            metrics = MetricsEngine(settings).calculate(result.plan, result.plan, scenario.vehicles)
        with _measure(result.timings, "serialization_ms"):
            serialized_size = len(json.dumps(_serializable_plan(result.plan), separators=(",", ":")))
        validation = validate_benchmark_route(result.plan, scenario.stops)
        result.timings["deterministic_total_ms"] = round(wall_ms, 3)
        instrumentation = getattr(result, "instrumentation", {}) or {}
        samples.append(
            {
                "repetition": repetition + 1,
                "wall_ms": round(wall_ms, 3),
                "cpu_ms": round(cpu_ms, 3),
                "cpu_utilization_percent": round(cpu_ms / wall_ms * 100 if wall_ms else 0.0, 3),
                "rss_before_mb": round(rss_before / 1_048_576, 3),
                "rss_after_mb": round(rss_after / 1_048_576, 3),
                "rss_delta_mb": round((rss_after - rss_before) / 1_048_576, 3),
                "peak_rss_mb": round(_peak_rss_mb(), 3),
                "serialized_bytes": serialized_size,
                "stage_timings": dict(result.timings),
                "distance_km": result.plan.total_distance_km,
                "metrics": metrics,
                "validation": validation,
                "local_search": instrumentation,
            }
        )
    wall_samples = [item["wall_ms"] for item in samples]
    cpu_samples = [item["cpu_ms"] for item in samples]
    stage_statistics = {stage: _stats([sample["stage_timings"][stage] for sample in samples]) for stage in STAGES}
    first = samples[0]
    return {
        "algorithm": strategy,
        "latency_ms": _stats(wall_samples),
        "cpu_ms": _stats(cpu_samples),
        "stage_statistics_ms": stage_statistics,
        "rss_peak_mb": round(max(sample["peak_rss_mb"] for sample in samples), 3),
        "rss_delta_mb": _stats([sample["rss_delta_mb"] for sample in samples]),
        "distance_km": first["distance_km"],
        "metrics": first["metrics"],
        "validation": first["validation"],
        "local_search_summary": _local_search_summary(samples),
        "samples": samples,
    }


def _legacy_workload(strategy: Mapping[str, Any], scenario: BenchmarkScenario) -> dict[str, Any]:
    return {
        "dataset": scenario.name,
        "dataset_version": scenario.version,
        "seed": scenario.seed,
        "stop_count": len(scenario.stops),
        "vehicle_count": len(scenario.vehicles),
        "algorithm": BASELINE_VERSION,
        "latency_ms": strategy["latency_ms"],
        "cpu_ms": strategy["cpu_ms"],
        "stage_statistics_ms": strategy["stage_statistics_ms"],
        "distance_km": strategy["distance_km"],
        "metrics": strategy["metrics"],
        "validation": strategy["validation"],
        "samples": strategy["samples"],
    }


def _comparison(baseline: Mapping[str, Any], optimized: Mapping[str, Any]) -> dict[str, Any]:
    baseline_latency = baseline["latency_ms"]
    optimized_latency = optimized["latency_ms"]
    baseline_metrics = baseline["metrics"]
    optimized_metrics = optimized["metrics"]
    return {
        "speedup": {key: _speedup(baseline_latency[key], optimized_latency[key]) for key in ("p50", "p95", "p99")},
        "quality_delta_percent": round(_percent_delta(baseline["distance_km"], optimized["distance_km"]), 3),
        "distance_delta_km": round(optimized["distance_km"] - baseline["distance_km"], 3),
        "fuel_delta_l": round(optimized_metrics["fuel_litres"]["after"] - baseline_metrics["fuel_litres"]["after"], 3),
        "co2_delta_kg": round(optimized_metrics["co2_kg"]["after"] - baseline_metrics["co2_kg"]["after"], 3),
        "driver_hours_delta": round(optimized_metrics["driver_hours"]["after"] - baseline_metrics["driver_hours"]["after"], 3),
        "correctness_equal": baseline["validation"]["valid"] == optimized["validation"]["valid"],
        "baseline_valid": baseline["validation"]["valid"],
        "optimized_valid": optimized["validation"]["valid"],
    }


def _baseline_workload(report: Mapping[str, Any] | None, stop_count: int) -> dict[str, Any] | None:
    if report is None:
        return None
    for workload in report.get("workloads", []):
        if workload.get("stop_count") == stop_count:
            if "strategies" in workload:
                return workload["strategies"].get(BASELINE_VERSION)
            return _legacy_baseline_workload(workload)
    raise ValueError(f"Baseline report does not contain workload {stop_count}")


def _legacy_baseline_workload(workload: Mapping[str, Any]) -> dict[str, Any]:
    samples = workload.get("samples", [])
    return {
        "algorithm": BASELINE_VERSION,
        "latency_ms": workload["latency_ms"],
        "cpu_ms": workload["cpu_ms"],
        "stage_statistics_ms": workload["stage_statistics_ms"],
        "rss_peak_mb": round(max((sample.get("peak_rss_mb", 0.0) for sample in samples), default=0.0), 3),
        "rss_delta_mb": _stats([sample.get("rss_delta_mb", 0.0) for sample in samples]) if samples else _stats([0.0]),
        "distance_km": workload["distance_km"],
        "metrics": workload["metrics"],
        "validation": workload["validation"],
        "local_search_summary": {"source": "legacy-baseline-report"},
        "samples": samples,
    }


def _strategy_runners(overrides: Mapping[str, StrategyRunner] | None) -> dict[str, StrategyRunner]:
    runners: dict[str, StrategyRunner] = {BASELINE_VERSION: run_baseline_v1}
    if overrides:
        runners.update(overrides)
    if OPTIMIZED_VERSION not in runners:
        module = importlib.import_module("app.benchmarks.optimized")
        from app.optimizer.optimized_v2 import OptimizedV2Strategy

        def optimized_runner(optimizer: RouteOptimizer, stops: Sequence[Any], vehicles: Sequence[Any], depot: Any) -> Any:
            return module.run_optimized_v2(OptimizedV2Strategy(optimizer), stops, vehicles, depot)

        runners[OPTIMIZED_VERSION] = optimized_runner
    return runners


def _local_search_summary(samples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counters = ("candidates_evaluated", "candidates_rejected", "candidates_pruned", "candidates_accepted", "iterations", "improvement_km", "optimization_wall_ms", "distance_cache_hits", "distance_cache_misses")
    summary: dict[str, Any] = {}
    for counter in counters:
        numeric = [float(sample.get("local_search", {}).get(counter)) for sample in samples if isinstance(sample.get("local_search", {}).get(counter), int | float)]
        if numeric:
            summary[counter] = _stats(numeric)
    budgets = [sample.get("local_search", {}).get("optimization_budget") for sample in samples if sample.get("local_search", {}).get("optimization_budget")]
    if budgets:
        summary["optimization_budget"] = budgets[0]
    stop_reasons = [sample.get("local_search", {}).get("stop_reason") for sample in samples if sample.get("local_search", {}).get("stop_reason")]
    if stop_reasons:
        summary["stop_reasons"] = sorted(set(stop_reasons))
    return summary


def _markdown(report: Mapping[str, Any]) -> str:
    if report.get("schema_version") == "greenmile-round2-benchmark-v1":
        return _legacy_markdown(report)
    lines = [
        "# Greenmile Round 2 Benchmark Comparison",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "| Stops | Baseline P50 | Optimized P50 | P50 Speedup | Baseline P95 | Optimized P95 | Quality Δ % | Correctness |",
        "|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for workload in report["workloads"]:
        strategies = workload["strategies"]
        baseline = strategies.get(BASELINE_VERSION)
        optimized = strategies.get(OPTIMIZED_VERSION)
        if baseline and optimized:
            comparison = workload["comparison"]
            correctness = "same" if comparison["correctness_equal"] else "changed"
            lines.append(
                f"| {workload['stop_count']:,} | {baseline['latency_ms']['p50']} | {optimized['latency_ms']['p50']} | "
                f"{comparison['speedup']['p50']}x | {baseline['latency_ms']['p95']} | {optimized['latency_ms']['p95']} | "
                f"{comparison['quality_delta_percent']} | {correctness} |"
            )
        else:
            only = next(iter(strategies.values()))
            lines.append(f"| {workload['stop_count']:,} | {only['latency_ms']['p50']} | — | — | {only['latency_ms']['p95']} | — | — | {'valid' if only['validation']['valid'] else 'invalid'} |")
    lines.extend(["", "## Local-search instrumentation", "", "| Stops | Evaluated P50 | Pruned P50 | Accepted P50 | Iterations P50 | Wall P50 ms |", "|---:|---:|---:|---:|---:|---:|"])
    for workload in report["workloads"]:
        optimized = workload["strategies"].get(OPTIMIZED_VERSION)
        if not optimized:
            continue
        summary = optimized.get("local_search_summary", {})
        def p50(key: str) -> object:
            value = summary.get(key)
            return value.get("p50", "—") if isinstance(value, Mapping) else "—"
        lines.append(f"| {workload['stop_count']:,} | {p50('candidates_evaluated')} | {p50('candidates_pruned')} | {p50('candidates_accepted')} | {p50('iterations')} | {p50('optimization_wall_ms')} |")
    return "\n".join(lines)


def _legacy_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Greenmile Round 2 Baseline Benchmark",
        "",
        "> Baseline infrastructure only. No optimizer change has been applied.",
        "",
        "| Stops | P50 ms | P95 ms | P99 ms | CPU P50 ms | Peak RSS MB | Distance km | Valid |",
        "|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for workload in report["workloads"]:
        latency = workload["latency_ms"]
        cpu = workload["cpu_ms"]
        peak = max(sample["peak_rss_mb"] for sample in workload["samples"])
        lines.append(
            f"| {workload['stop_count']:,} | {latency['p50']} | {latency['p95']} | {latency['p99']} | "
            f"{cpu['p50']} | {peak} | {workload['distance_km']} | {'yes' if workload['validation']['valid'] else 'no'} |"
        )
    return "\n".join(lines)


def _stats(samples: Sequence[float]) -> dict[str, float]:
    values = list(samples)
    return {"min": round(min(values), 3), "max": round(max(values), 3), "p50": nearest_rank(values, 50), "p95": nearest_rank(values, 95), "p99": nearest_rank(values, 99)}


class _measure:
    def __init__(self, timings: dict[str, float], key: str):
        self.timings, self.key = timings, key

    def __enter__(self) -> None:
        self.started = perf_counter()

    def __exit__(self, *_args: object) -> None:
        self.timings[self.key] = round((perf_counter() - self.started) * 1_000, 3)


def _serializable_plan(plan: Any) -> dict[str, Any]:
    return {
        "cluster_count": plan.cluster_count,
        "distance_km": plan.total_distance_km,
        "feasible": plan.constraints.feasible,
        "routes": [[{"id": item.external_id, "sequence": item.sequence_number, "distance_km": item.distance_from_previous_km} for item in route] for route in plan.routes],
    }


def _speedup(baseline_ms: float, optimized_ms: float) -> float:
    return round(baseline_ms / optimized_ms, 3) if optimized_ms else 0.0


def _percent_delta(baseline: float, optimized: float) -> float:
    return (optimized / baseline - 1) * 100 if baseline else 0.0


def _environment() -> dict[str, object]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpu_count": psutil.cpu_count(),
        "physical_cpu_count": psutil.cpu_count(logical=False),
        "memory_total_mb": round(psutil.virtual_memory().total / 1_048_576, 3),
    }


def _peak_rss_mb() -> float:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / 1_048_576 if sys.platform == "darwin" else value / 1024


def _git_sha() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, check=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
