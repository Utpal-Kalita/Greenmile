from __future__ import annotations

from dataclasses import replace

from app.benchmarks.baseline import run_baseline_v1
from app.benchmarks.datasets import generate_scenario
from app.benchmarks.optimized import OPTIMIZED_VERSION, run_optimized_v2
from app.benchmarks.validation import validate_benchmark_route
from app.core.config import Settings
from app.optimizer.engine import HaversineProvider, Location, RouteOptimizer
from app.optimizer.optimized_v2 import DistanceOracle, OptimizedV2Strategy, TwoOptBudget, two_opt_delta
from tests.test_optimizer import StubStop, StubVehicle


def _segment_distance(order: list[int], oracle: DistanceOracle) -> float:
    points = [0, *(index + 1 for index in order), 0]
    return sum(oracle.distance(points[index - 1], points[index]) for index in range(1, len(points)))


def test_distance_oracle_caches_repeated_distances():
    stops = [StubStop("D1", "DELIVERY", 28.53, 77.21), StubStop("D2", "DELIVERY", 28.54, 77.22)]
    oracle = DistanceOracle(HaversineProvider(), Location(28.5355, 77.2732), stops)

    first = oracle.distance(0, 1)
    second = oracle.distance(1, 0)

    assert first == second
    assert oracle.cache_misses == 1
    assert oracle.cache_hits == 1


def test_two_opt_delta_matches_full_distance_improvement():
    stops = [
        StubStop("A", "DELIVERY", 28.50, 77.20),
        StubStop("B", "DELIVERY", 28.60, 77.20),
        StubStop("C", "DELIVERY", 28.50, 77.30),
        StubStop("D", "DELIVERY", 28.60, 77.30),
    ]
    origin = Location(28.55, 77.25)
    oracle = DistanceOracle(HaversineProvider(), origin, stops)
    before = [0, 3, 1, 2]
    before_distance = _segment_distance(before, oracle)

    after, stats = two_opt_delta(before, oracle, TwoOptBudget(max_iterations=20, forward_candidate_window=25))
    after_distance = _segment_distance(after, oracle)

    assert after_distance <= before_distance
    assert stats.candidates_evaluated > 0
    assert stats.iterations > 0
    assert stats.optimization_wall_ms >= 0


def test_optimized_v2_preserves_stop_completeness_and_depot_constraints():
    scenario = generate_scenario(100, seed=20260823)
    optimizer = RouteOptimizer(HaversineProvider(), Settings())
    baseline = run_baseline_v1(optimizer, scenario.stops, scenario.vehicles, scenario.depot)
    optimized = run_optimized_v2(OptimizedV2Strategy(optimizer), scenario.stops, scenario.vehicles, scenario.depot)

    assert optimized.plan.constraints.feasible == baseline.plan.constraints.feasible
    assert validate_benchmark_route(optimized.plan, scenario.stops)["valid"]
    assert [item.external_id for item in optimized.plan.stops if item.stop] != []
    assert sorted(item.external_id for item in optimized.plan.stops if item.stop) == sorted(stop.external_id for stop in scenario.stops)
    assert optimized.plan.stops[0].external_id == "DEPOT"
    assert optimized.plan.stops[-1].external_id == "DEPOT"
    assert optimized.plan.total_distance_km <= baseline.plan.total_distance_km * 1.06
    assert optimized.instrumentation["candidates_evaluated"] > 0


def test_optimized_v2_benchmark_adapter_reports_version_and_stats():
    scenario = generate_scenario(100, seed=42)
    optimizer = RouteOptimizer(HaversineProvider(), Settings())
    result = run_optimized_v2(OptimizedV2Strategy(optimizer), scenario.stops, scenario.vehicles, scenario.depot)

    assert OPTIMIZED_VERSION == "optimized-v2"
    assert result.instrumentation["optimization_budget"]
    assert result.instrumentation["candidates_rejected"] >= 0
    assert result.timings["local_optimization_ms"] >= 0


def test_optimized_v2_validator_rejects_duplicate_route_stop():
    scenario = generate_scenario(100, seed=42)
    optimizer = RouteOptimizer(HaversineProvider(), Settings())
    result = OptimizedV2Strategy(optimizer).optimize(scenario.stops, scenario.vehicles, scenario.depot)
    route = result.plan.routes[0]
    first = next(item for item in route if item.stop is not None)
    route.insert(-1, replace(first, sequence_number=9999))

    validation = optimizer.validate(scenario.stops, result.plan.routes, scenario.vehicles, scenario.depot)

    assert not validation.feasible
    assert any(item.type == "DUPLICATE_STOP" for item in validation.violations)
