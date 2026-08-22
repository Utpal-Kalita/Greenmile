from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.benchmarks.timing import StageTimer
from app.optimizer.engine import Location, RoutePlan, StopLike, VehicleLike
from app.optimizer.optimized_v2 import LocalSearchStats, OptimizedV2Strategy

OPTIMIZED_VERSION = "optimized-v2"


@dataclass(frozen=True)
class OptimizedBenchmarkResult:
    plan: RoutePlan
    timings: dict[str, float]
    instrumentation: dict[str, object]


def run_optimized_v2(
    strategy: OptimizedV2Strategy,
    stops: Sequence[StopLike],
    vehicles: Sequence[VehicleLike],
    depot: Location,
) -> OptimizedBenchmarkResult:
    """Run optimized-v2 behind a benchmark adapter without touching baseline-v1."""
    timer = StageTimer()
    with timer.measure("validation_ms"):
        if not stops or not vehicles:
            raise ValueError("Stops and vehicles are required")
    with timer.measure("clustering_ms"):
        labels = strategy.optimizer._clusters(stops)
        clustered = sorted(zip(stops, labels, strict=True), key=lambda value: (value[1], value[0].external_id))
        groups = strategy.optimizer._partition([item[0] for item in clustered], len(vehicles))

    routes = []
    sequence = 0
    local_search = LocalSearchStats()
    for vehicle_index, group in enumerate(groups, start=1):
        deliveries = [stop for stop in group if stop.type.value == "DELIVERY"]
        returns = [stop for stop in group if stop.type.value != "DELIVERY"]
        with timer.measure("route_construction_ms"):
            delivery_ordered, delivery_stats = strategy._optimize_segment(deliveries, depot)
            return_origin = delivery_ordered[-1] if delivery_ordered else depot
            return_ordered, return_stats = strategy._optimize_segment(returns, return_origin)
        local_search.absorb(delivery_stats)
        local_search.absorb(return_stats)
        # _optimize_segment includes nearest-neighbour and local search. Attribute
        # only the measured local-search part to local_optimization_ms so stage
        # totals preserve the critical-path taxonomy.
        timer.timings["local_optimization_ms"] += round(delivery_stats.optimization_wall_ms + return_stats.optimization_wall_ms, 3)
        timer.timings["route_construction_ms"] = round(max(0.0, timer.timings["route_construction_ms"] - delivery_stats.optimization_wall_ms - return_stats.optimization_wall_ms), 3)
        with timer.measure("distance_calculation_ms"):
            route, sequence = strategy.optimizer._materialize(
                delivery_ordered + return_ordered,
                vehicles[vehicle_index - 1],
                depot,
                vehicle_index,
                sequence,
            )
        routes.append(route)
    with timer.measure("constraint_validation_ms"):
        constraints = strategy.optimizer.validate(stops, routes, vehicles, depot, total_distance_km=round(strategy.optimizer._routes_distance(routes), 3))
    with timer.measure("distance_calculation_ms"):
        distance = round(strategy.optimizer._routes_distance(routes), 3)
    return OptimizedBenchmarkResult(RoutePlan(routes, len(set(labels)), distance, constraints), timer.timings, local_search.as_dict())
