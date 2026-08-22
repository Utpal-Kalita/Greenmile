from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.benchmarks.timing import StageTimer
from app.optimizer.engine import Location, RouteOptimizer, RoutePlan, StopLike, VehicleLike

BASELINE_VERSION = "baseline-v1"


@dataclass(frozen=True)
class BaselineResult:
    plan: RoutePlan
    timings: dict[str, float]


def run_baseline_v1(
    optimizer: RouteOptimizer,
    stops: Sequence[StopLike],
    vehicles: Sequence[VehicleLike],
    depot: Location,
) -> BaselineResult:
    """Run the current algorithm unchanged behind a stable benchmark version."""
    timer = StageTimer()
    with timer.measure("validation_ms"):
        if not stops or not vehicles:
            raise ValueError("Stops and vehicles are required")
    with timer.measure("clustering_ms"):
        labels = optimizer._clusters(stops)
        clustered = sorted(zip(stops, labels, strict=True), key=lambda value: (value[1], value[0].external_id))
        groups = optimizer._partition([item[0] for item in clustered], len(vehicles))
    routes = []
    sequence = 0
    for vehicle_index, group in enumerate(groups, start=1):
        deliveries = [stop for stop in group if stop.type.value == "DELIVERY"]
        returns = [stop for stop in group if stop.type.value != "DELIVERY"]
        with timer.measure("route_construction_ms"):
            ordered_deliveries = _nearest_neighbour(optimizer, deliveries, depot, timer)
            return_origin = ordered_deliveries[-1] if ordered_deliveries else depot
            ordered_returns = _nearest_neighbour(optimizer, returns, return_origin, timer)
        with timer.measure("local_optimization_ms"):
            ordered_deliveries = optimizer._two_opt(ordered_deliveries, depot)
            ordered_returns = optimizer._two_opt(ordered_returns, return_origin)
        with timer.measure("distance_calculation_ms"):
            route, sequence = optimizer._materialize(
                ordered_deliveries + ordered_returns,
                vehicles[vehicle_index - 1],
                depot,
                vehicle_index,
                sequence,
            )
        routes.append(route)
    with timer.measure("constraint_validation_ms"):
        constraints = optimizer.check_constraints(routes, vehicles, depot)
    with timer.measure("distance_calculation_ms"):
        distance = round(optimizer._routes_distance(routes), 3)
    return BaselineResult(RoutePlan(routes, len(set(labels)), distance, constraints), timer.timings)


def _nearest_neighbour(
    optimizer: RouteOptimizer,
    stops: list[StopLike],
    origin: Location | StopLike,
    timer: StageTimer,
) -> list[StopLike]:
    unvisited = list(stops)
    route: list[StopLike] = []
    current = origin
    while unvisited:
        with timer.measure("distance_calculation_ms"):
            nearest = min(unvisited, key=lambda stop: (optimizer.provider.distance(current, stop), stop.external_id))
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest
    return route
