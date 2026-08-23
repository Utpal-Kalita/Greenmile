from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Protocol

from app.core.config import Settings
from app.domain.enums import StopType
from app.optimizer.engine import ConstraintCheck, HaversineProvider, Location, PlannedStop, RouteOptimizer, RoutePlan, RoutingProvider, StopLike, VehicleLike, Violation

OPTIMIZED_VERSION = "optimized-v2"


class PointLike(Protocol):
    external_id: str
    lat: float
    lng: float


@dataclass(frozen=True)
class TwoOptBudget:
    max_iterations: int
    forward_candidate_window: int = 25
    min_improvement_km: float = 1e-9
    max_candidate_multiplier: int = 2

    def max_candidates(self, stop_count: int) -> int:
        per_iteration = max(1, stop_count * max(1, self.forward_candidate_window))
        return max(1, self.max_iterations * per_iteration * self.max_candidate_multiplier)

    def as_dict(self, stop_count: int | None = None) -> dict[str, int | float | None]:
        return {
            "max_iterations": self.max_iterations,
            "forward_candidate_window": self.forward_candidate_window,
            "min_improvement_km": self.min_improvement_km,
            "max_candidate_multiplier": self.max_candidate_multiplier,
            "max_candidates": self.max_candidates(stop_count) if stop_count is not None else None,
        }


@dataclass(frozen=True)
class LocalSearchIteration:
    iteration: int
    candidates_evaluated: int
    candidates_rejected: int
    candidates_pruned: int
    candidates_accepted: int
    improvement_km: float


@dataclass
class LocalSearchStats:
    candidates_evaluated: int = 0
    candidates_rejected: int = 0
    candidates_pruned: int = 0
    candidates_accepted: int = 0
    iterations: int = 0
    improvement_km: float = 0.0
    optimization_budget: dict[str, int | float | None] = field(default_factory=dict)
    optimization_wall_ms: float = 0.0
    stop_reason: str = "not_started"
    distance_cache_hits: int = 0
    distance_cache_misses: int = 0
    iteration_improvements: list[LocalSearchIteration] = field(default_factory=list)

    def absorb(self, other: LocalSearchStats) -> None:
        offset = self.iterations
        self.candidates_evaluated += other.candidates_evaluated
        self.candidates_rejected += other.candidates_rejected
        self.candidates_pruned += other.candidates_pruned
        self.candidates_accepted += other.candidates_accepted
        self.iterations += other.iterations
        self.improvement_km = round(self.improvement_km + other.improvement_km, 6)
        self.optimization_wall_ms = round(self.optimization_wall_ms + other.optimization_wall_ms, 3)
        self.distance_cache_hits += other.distance_cache_hits
        self.distance_cache_misses += other.distance_cache_misses
        self.iteration_improvements.extend(
            LocalSearchIteration(
                iteration=item.iteration + offset,
                candidates_evaluated=item.candidates_evaluated,
                candidates_rejected=item.candidates_rejected,
                candidates_pruned=item.candidates_pruned,
                candidates_accepted=item.candidates_accepted,
                improvement_km=item.improvement_km,
            )
            for item in other.iteration_improvements
        )
        if other.stop_reason != "not_started":
            self.stop_reason = other.stop_reason
        if not self.optimization_budget:
            self.optimization_budget = other.optimization_budget

    def as_dict(self) -> dict[str, object]:
        return {
            "candidates_evaluated": self.candidates_evaluated,
            "candidates_rejected": self.candidates_rejected,
            "candidates_pruned": self.candidates_pruned,
            "candidates_accepted": self.candidates_accepted,
            "iterations": self.iterations,
            "improvement_km": round(self.improvement_km, 6),
            "optimization_budget": self.optimization_budget,
            "optimization_wall_ms": self.optimization_wall_ms,
            "stop_reason": self.stop_reason,
            "distance_cache_hits": self.distance_cache_hits,
            "distance_cache_misses": self.distance_cache_misses,
            "iteration_improvements": [vars(item) for item in self.iteration_improvements],
        }


@dataclass(frozen=True)
class OptimizedV2Result:
    plan: RoutePlan
    local_search: LocalSearchStats


class DistanceOracle:
    """Cached distance oracle for one ordered local-search segment."""

    def __init__(self, provider: RoutingProvider, origin: Location | StopLike, stops: list[StopLike]):
        self.provider = provider
        self.points: list[Location | StopLike] = [origin, *stops]
        self._cache: dict[tuple[int, int], float] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def distance(self, first: int, second: int) -> float:
        if first == second:
            return 0.0
        key = (first, second) if first < second else (second, first)
        cached = self._cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return cached
        self.cache_misses += 1
        value = self.provider.distance(self.points[first], self.points[second])
        self._cache[key] = value
        return value


class OptimizedV2Strategy:
    """Same route semantics as baseline-v1 with cached constant-time 2-opt deltas."""

    def __init__(self, optimizer: RouteOptimizer, *, budget: TwoOptBudget | None = None):
        self.optimizer = optimizer
        self.budget = budget or TwoOptBudget(max_iterations=optimizer.settings.two_opt_max_iterations)

    def optimize(self, stops: list[StopLike] | tuple[StopLike, ...], vehicles: list[VehicleLike] | tuple[VehicleLike, ...], depot: Location) -> OptimizedV2Result:
        if not stops or not vehicles:
            plan = RoutePlan([], 0, 0.0, ConstraintCheck(False, [Violation("INPUT", "Stops and vehicles are required")]))
            return OptimizedV2Result(plan, LocalSearchStats(stop_reason="invalid_input"))

        stop_list = list(stops)
        cluster_labels = self.optimizer._clusters(stop_list)
        clustered = sorted(zip(stop_list, cluster_labels, strict=True), key=lambda value: (value[1], value[0].external_id))
        groups = self.optimizer._partition([item[0] for item in clustered], len(vehicles))
        routes: list[list[PlannedStop]] = []
        sequence = 0
        local_search = LocalSearchStats()

        for vehicle_index, group in enumerate(groups, start=1):
            deliveries = [stop for stop in group if stop.type == StopType.DELIVERY]
            returns = [stop for stop in group if stop.type != StopType.DELIVERY]
            ordered_deliveries, delivery_stats = self._optimize_segment(deliveries, depot)
            local_search.absorb(delivery_stats)
            return_origin = ordered_deliveries[-1] if ordered_deliveries else depot
            ordered_returns, return_stats = self._optimize_segment(returns, return_origin)
            local_search.absorb(return_stats)
            route, sequence = self.optimizer._materialize(ordered_deliveries + ordered_returns, vehicles[vehicle_index - 1], depot, vehicle_index, sequence)
            routes.append(route)

        total_distance = round(self.optimizer._routes_distance(routes), 3)
        constraints = self.optimizer.validate(stop_list, routes, vehicles, depot, total_distance_km=total_distance)
        return OptimizedV2Result(RoutePlan(routes, len(set(cluster_labels)), total_distance, constraints), local_search)

    def _optimize_segment(self, stops: list[StopLike], origin: Location | StopLike) -> tuple[list[StopLike], LocalSearchStats]:
        if len(stops) < 2:
            return list(stops), LocalSearchStats(stop_reason="segment_too_small", optimization_budget=self.budget.as_dict(len(stops)))
        oracle = DistanceOracle(self.optimizer.provider, origin, stops)
        nearest_order = self._nearest_neighbour(stops, oracle)
        optimized_order, stats = two_opt_delta(nearest_order, oracle, self.budget)
        stats.distance_cache_hits = oracle.cache_hits
        stats.distance_cache_misses = oracle.cache_misses
        return [stops[index] for index in optimized_order], stats

    def _nearest_neighbour(self, stops: list[StopLike], oracle: DistanceOracle) -> list[int]:
        unvisited = set(range(len(stops)))
        route: list[int] = []
        current_node = 0
        while unvisited:
            nearest = min(unvisited, key=lambda index: (oracle.distance(current_node, index + 1), stops[index].external_id))
            route.append(nearest)
            unvisited.remove(nearest)
            current_node = nearest + 1
        return route


def two_opt_delta(order: list[int], oracle: DistanceOracle, budget: TwoOptBudget) -> tuple[list[int], LocalSearchStats]:
    """2-opt first-improvement search using constant-time edge deltas.

    The loop bounds intentionally mirror RouteOptimizer._two_opt so optimized-v2
    preserves baseline-v1 route semantics while avoiding repeated Haversine work.
    """
    started = perf_counter()
    route = list(order)
    max_candidates = budget.max_candidates(len(route))
    stats = LocalSearchStats(optimization_budget=budget.as_dict(len(route)))
    if len(route) < 3:
        stats.stop_reason = "segment_too_small"
        stats.optimization_wall_ms = round((perf_counter() - started) * 1_000, 3)
        return route, stats

    for iteration in range(1, budget.max_iterations + 1):
        improved = False
        iteration_evaluated = 0
        iteration_rejected = 0
        iteration_pruned = 0
        iteration_accepted = 0
        iteration_improvement = 0.0
        for left in range(len(route) - 2):
            previous_node = 0 if left == 0 else route[left - 1] + 1
            left_node = route[left] + 1
            for right in range(left + 2, min(len(route), left + budget.forward_candidate_window + 2)):
                if stats.candidates_evaluated >= max_candidates:
                    stats.stop_reason = "candidate_budget_exhausted"
                    stats.iterations = iteration
                    stats.iteration_improvements.append(LocalSearchIteration(iteration, iteration_evaluated, iteration_rejected, iteration_pruned, iteration_accepted, round(iteration_improvement, 6)))
                    stats.optimization_wall_ms = round((perf_counter() - started) * 1_000, 3)
                    return route, stats

                right_node = route[right - 1] + 1
                following_node = 0 if right == len(route) else route[right] + 1
                old_edges = oracle.distance(previous_node, left_node) + oracle.distance(right_node, following_node)

                # Spatially informed safe pruning: if either proposed replacement
                # edge is already at least as long as both old edges combined,
                # the positive second edge cannot produce an improvement.
                first_replacement = oracle.distance(previous_node, right_node)
                if first_replacement >= old_edges:
                    stats.candidates_pruned += 1
                    stats.candidates_rejected += 1
                    iteration_pruned += 1
                    iteration_rejected += 1
                    continue
                second_replacement = oracle.distance(left_node, following_node)
                if second_replacement >= old_edges:
                    stats.candidates_pruned += 1
                    stats.candidates_rejected += 1
                    iteration_pruned += 1
                    iteration_rejected += 1
                    continue

                delta = first_replacement + second_replacement - old_edges
                stats.candidates_evaluated += 1
                iteration_evaluated += 1
                if delta < -budget.min_improvement_km:
                    route[left:right] = reversed(route[left:right])
                    improvement = -delta
                    stats.candidates_accepted += 1
                    stats.improvement_km = round(stats.improvement_km + improvement, 6)
                    iteration_accepted += 1
                    iteration_improvement += improvement
                    improved = True
                    break
                stats.candidates_rejected += 1
                iteration_rejected += 1
            if improved:
                break
        stats.iterations = iteration
        stats.iteration_improvements.append(LocalSearchIteration(iteration, iteration_evaluated, iteration_rejected, iteration_pruned, iteration_accepted, round(iteration_improvement, 6)))
        if not improved:
            stats.stop_reason = "no_improvement"
            break
        if iteration_improvement < budget.min_improvement_km:
            stats.stop_reason = "improvement_below_threshold"
            break
    else:
        stats.stop_reason = "iteration_budget_exhausted"

    stats.optimization_wall_ms = round((perf_counter() - started) * 1_000, 3)
    return route, stats


def run_optimized_v2(stops: list[StopLike] | tuple[StopLike, ...], vehicles: list[VehicleLike] | tuple[VehicleLike, ...], depot: Location, settings: Settings | None = None, provider: RoutingProvider | None = None) -> OptimizedV2Result:
    optimizer = RouteOptimizer(provider or HaversineProvider(), settings or Settings())
    return OptimizedV2Strategy(optimizer).optimize(stops, vehicles, depot)
