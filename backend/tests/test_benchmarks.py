from app.benchmarks.baseline import BASELINE_VERSION
from app.benchmarks.datasets import REQUIRED_WORKLOADS, generate_scenario
from app.benchmarks.harness import OPTIMIZED_VERSION, BenchmarkConfig, nearest_rank, run_benchmarks


def test_dataset_generation_is_deterministic_and_complete():
    first = generate_scenario(100, seed=42)
    second = generate_scenario(100, seed=42)
    assert REQUIRED_WORKLOADS == (100, 500, 1_000, 2_500, 5_000)
    assert first == second
    assert len(first.stops) == 100
    assert len({stop.external_id for stop in first.stops}) == 100
    assert len({stop.id for stop in first.stops}) == 100


def test_nearest_rank_uses_observed_samples():
    samples = [1.0, 2.0, 3.0, 4.0, 100.0]
    assert nearest_rank(samples, 50) == 3.0
    assert nearest_rank(samples, 95) == 100.0
    assert nearest_rank(samples, 99) == 100.0


def test_quick_benchmark_emits_machine_readable_stage_samples():
    report = run_benchmarks(BenchmarkConfig(workloads=(100,), warmups=0, repetitions=2, seed=42))
    workload = report["workloads"][0]
    assert report["algorithm_changed"] is False
    assert workload["algorithm"] == BASELINE_VERSION
    assert workload["validation"]["required_stop_count"] == 100
    assert len(workload["samples"]) == 2
    assert workload["latency_ms"]["p99"] in [item["wall_ms"] for item in workload["samples"]]
    assert set(workload["stage_statistics_ms"]) == {
        "request_parsing_ms",
        "database_access_ms",
        "validation_ms",
        "clustering_ms",
        "distance_calculation_ms",
        "route_construction_ms",
        "local_optimization_ms",
        "constraint_validation_ms",
        "metrics_ms",
        "persistence_ms",
        "serialization_ms",
        "deterministic_total_ms",
    }


def test_comparison_benchmark_loads_preserved_baseline():
    baseline_report = run_benchmarks(BenchmarkConfig(workloads=(100,), warmups=0, repetitions=1, seed=42))

    report = run_benchmarks(
        BenchmarkConfig(workloads=(100,), warmups=0, repetitions=1, seed=42, strategies=(OPTIMIZED_VERSION,)),
        compare_baseline=baseline_report,
    )
    workload = report["workloads"][0]

    assert report["baseline_preserved"] is True
    assert BASELINE_VERSION in workload["strategies"]
    assert OPTIMIZED_VERSION in workload["strategies"]
    assert workload["comparison"]["speedup"]["p50"] > 0
    assert workload["strategies"][OPTIMIZED_VERSION]["local_search_summary"]["candidates_evaluated"]["p50"] > 0
