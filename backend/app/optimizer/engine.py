from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Protocol

from sklearn.cluster import DBSCAN

from app.core.config import Settings
from app.domain.enums import RouteAction, StopType


class StopLike(Protocol):
    id: object
    external_id: str
    type: StopType
    address: str
    lat: float
    lng: float
    weight_kg: float
    volume_l: float
    time_window_start: time
    time_window_end: time
    service_time_seconds: int


class VehicleLike(Protocol):
    id: object
    vehicle_code: str
    capacity_kg: float
    capacity_l: float
    fuel_efficiency_km_per_l: float
    driver_hourly_cost: float


@dataclass(frozen=True)
class Location:
    lat: float
    lng: float


@dataclass
class PlannedStop:
    stop: StopLike | None
    external_id: str
    name: str
    address: str
    lat: float
    lng: float
    type: StopType | str
    action: RouteAction
    vehicle_sequence: int
    sequence_number: int
    arrival_time: datetime
    departure_time: datetime
    load_before_kg: float
    load_after_kg: float
    load_before_l: float
    load_after_l: float
    distance_from_previous_km: float


@dataclass
class Violation:
    type: str
    message: str
    stop_id: str | None = None
    amount_kg: float | None = None
    amount_l: float | None = None


@dataclass
class ConstraintCheck:
    feasible: bool
    violations: list[Violation] = field(default_factory=list)


@dataclass
class RoutePlan:
    routes: list[list[PlannedStop]]
    cluster_count: int
    total_distance_km: float
    constraints: ConstraintCheck

    @property
    def stops(self) -> list[PlannedStop]:
        return [stop for route in self.routes for stop in route]


@dataclass
class IncrementalRepair:
    plan: RoutePlan
    affected_vehicle_sequence: int | None
    removed_stop_ids: list[str]
    previous_stop_ids: list[str]
    updated_stop_ids: list[str]
    changed_segment_stop_ids: list[str]


class RoutingProvider(Protocol):
    name: str

    def distance(self, first: Location | StopLike, second: Location | StopLike) -> float: ...


class HaversineProvider:
    name = "HAVERSINE"

    def distance(self, first: Location | StopLike, second: Location | StopLike) -> float:
        radius_km = 6371.0088
        lat1, lng1, lat2, lng2 = map(radians, (first.lat, first.lng, second.lat, second.lng))
        delta_lat = lat2 - lat1
        delta_lng = lng2 - lng1
        value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lng / 2) ** 2
        return radius_km * 2 * asin(sqrt(value))


class RouteOptimizer:
    def __init__(self, provider: RoutingProvider, settings: Settings):
        self.provider = provider
        self.settings = settings

    def baseline(self, stops: Sequence[StopLike], vehicles: Sequence[VehicleLike], depot: Location) -> RoutePlan:
        deliveries = [stop for stop in stops if stop.type == StopType.DELIVERY]
        returns = [stop for stop in stops if stop.type != StopType.DELIVERY]
        routes: list[list[PlannedStop]] = []
        sequence = 0
        for vehicle_index, vehicle_stops in enumerate(self._partition(deliveries, len(vehicles)), start=1):
            route, sequence = self._plan_segment(vehicle_stops, vehicles[vehicle_index - 1], depot, vehicle_index, sequence, close_depot=True, nearest=False)
            routes.append(route)
        for vehicle_index, vehicle_stops in enumerate(self._partition(returns, len(vehicles)), start=1):
            route, sequence = self._plan_segment(vehicle_stops, vehicles[vehicle_index - 1], depot, vehicle_index, sequence, close_depot=True, nearest=False)
            routes.append(route)
        constraints = self.check_constraints(routes, vehicles, depot)
        return RoutePlan(routes, 1, round(self._routes_distance(routes), 3), constraints)

    def optimize(self, stops: Sequence[StopLike], vehicles: Sequence[VehicleLike], depot: Location) -> RoutePlan:
        if not stops or not vehicles:
            return RoutePlan([], 0, 0.0, ConstraintCheck(False, [Violation("INPUT", "Stops and vehicles are required")]))
        cluster_labels = self._clusters(stops)
        clustered = sorted(zip(stops, cluster_labels, strict=True), key=lambda value: (value[1], value[0].external_id))
        groups = self._partition([item[0] for item in clustered], len(vehicles))
        routes: list[list[PlannedStop]] = []
        sequence = 0
        for vehicle_index, group in enumerate(groups, start=1):
            ordered_deliveries = self._optimize_segment([stop for stop in group if stop.type == StopType.DELIVERY], depot)
            ordered_returns = self._optimize_segment([stop for stop in group if stop.type != StopType.DELIVERY], ordered_deliveries[-1] if ordered_deliveries else depot)
            route, sequence = self._materialize(ordered_deliveries + ordered_returns, vehicles[vehicle_index - 1], depot, vehicle_index, sequence)
            routes.append(route)
        constraints = self.check_constraints(routes, vehicles, depot)
        return RoutePlan(routes, len(set(cluster_labels)), round(self._routes_distance(routes), 3), constraints)

    def _clusters(self, stops: Sequence[StopLike]) -> list[int]:
        if len(stops) < self.settings.dbscan_min_samples:
            return [0] * len(stops)
        coordinates = [[radians(stop.lat), radians(stop.lng)] for stop in stops]
        labels = DBSCAN(
            eps=self.settings.dbscan_eps_km / 6371.0088,
            min_samples=self.settings.dbscan_min_samples,
            metric="haversine",
            algorithm="ball_tree",
        ).fit_predict(coordinates)
        highest = max((int(label) for label in labels if label >= 0), default=-1)
        return [int(label) if label >= 0 else highest + index + 1 for index, label in enumerate(labels)]

    def _partition(self, stops: Sequence[StopLike], count: int) -> list[list[StopLike]]:
        result: list[list[StopLike]] = [[] for _ in range(count)]
        loads = [(0.0, 0.0) for _ in range(count)]
        for stop in sorted(stops, key=lambda item: (item.type.value, -item.weight_kg, item.external_id)):
            index = min(range(count), key=lambda value: (loads[value][0], loads[value][1], value))
            result[index].append(stop)
            loads[index] = (loads[index][0] + stop.weight_kg, loads[index][1] + stop.volume_l)
        return result

    def _optimize_segment(self, stops: list[StopLike], origin: Location | StopLike) -> list[StopLike]:
        if len(stops) < 2:
            return list(stops)
        unvisited = list(stops)
        route: list[StopLike] = []
        current = origin
        while unvisited:
            nearest = min(unvisited, key=lambda stop: (self.provider.distance(current, stop), stop.external_id))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        return self._two_opt(route, origin)

    def _two_opt(self, route: list[StopLike], origin: Location | StopLike) -> list[StopLike]:
        best = list(route)
        if len(best) < 3:
            return best
        for _ in range(self.settings.two_opt_max_iterations):
            improved = False
            for left in range(len(best) - 2):
                previous: Location | StopLike = origin if left == 0 else best[left - 1]
                for right in range(left + 2, min(len(best), left + 27)):
                    following: Location | StopLike = origin if right == len(best) else best[right]
                    old_edges = self.provider.distance(previous, best[left]) + self.provider.distance(best[right - 1], following)
                    new_edges = self.provider.distance(previous, best[right - 1]) + self.provider.distance(best[left], following)
                    if new_edges + 1e-9 < old_edges:
                        best[left:right] = reversed(best[left:right])
                        improved = True
                        break
                if improved:
                    break
            if not improved:
                break
        return best

    def _sequence_distance(self, route: Sequence[StopLike], origin: Location | StopLike) -> float:
        points: list[Location | StopLike] = [origin, *route, origin]
        return sum(self.provider.distance(points[index - 1], points[index]) for index in range(1, len(points)))

    def _plan_segment(self, stops: list[StopLike], vehicle: VehicleLike, depot: Location, vehicle_sequence: int, sequence: int, *, close_depot: bool, nearest: bool) -> tuple[list[PlannedStop], int]:
        del close_depot
        ordered = self._optimize_segment(stops, depot) if nearest else list(stops)
        return self._materialize(ordered, vehicle, depot, vehicle_sequence, sequence)

    def _materialize(self, route: list[StopLike], vehicle: VehicleLike, depot: Location, vehicle_sequence: int, global_sequence: int) -> tuple[list[PlannedStop], int]:
        day = date.today()
        current_time = datetime.combine(day, time(8, 0))
        delivery_kg = sum(stop.weight_kg for stop in route if stop.type == StopType.DELIVERY)
        delivery_l = sum(stop.volume_l for stop in route if stop.type == StopType.DELIVERY)
        current_kg, current_l = delivery_kg, delivery_l
        planned = [PlannedStop(None, "DEPOT", "Depot", "Depot", depot.lat, depot.lng, "WAREHOUSE", RouteAction.DEPOT_START, vehicle_sequence, global_sequence, current_time, current_time, current_kg, current_kg, current_l, current_l, 0.0)]
        global_sequence += 1
        previous: Location | StopLike = depot
        for stop in route:
            distance = self.provider.distance(previous, stop)
            current_time += timedelta(hours=distance / self.settings.average_speed_kmh)
            window_start = datetime.combine(day, stop.time_window_start)
            if current_time < window_start:
                current_time = window_start
            arrival = current_time
            before_kg, before_l = current_kg, current_l
            if stop.type == StopType.DELIVERY:
                current_kg -= stop.weight_kg
                current_l -= stop.volume_l
                action = RouteAction.DELIVER
            else:
                current_kg += stop.weight_kg
                current_l += stop.volume_l
                action = RouteAction.RETURN if stop.type == StopType.RETURN else RouteAction.PICKUP
            current_time += timedelta(seconds=stop.service_time_seconds)
            planned.append(PlannedStop(stop, stop.external_id, stop.address.split(",")[1].strip() if "," in stop.address else stop.external_id, stop.address, stop.lat, stop.lng, stop.type, action, vehicle_sequence, global_sequence, arrival, current_time, before_kg, current_kg, before_l, current_l, distance))
            global_sequence += 1
            previous = stop
        distance_home = self.provider.distance(previous, depot)
        current_time += timedelta(hours=distance_home / self.settings.average_speed_kmh)
        planned.append(PlannedStop(None, "DEPOT", "Depot", "Depot", depot.lat, depot.lng, "WAREHOUSE", RouteAction.DEPOT_END, vehicle_sequence, global_sequence, current_time, current_time, current_kg, current_kg, current_l, current_l, distance_home))
        return planned, global_sequence + 1

    def check_constraints(self, routes: Sequence[Sequence[PlannedStop]], vehicles: Sequence[VehicleLike], depot: Location) -> ConstraintCheck:
        violations: list[Violation] = []
        for route_index, route in enumerate(routes):
            if not route:
                continue
            vehicle = vehicles[min(route_index, len(vehicles) - 1)]
            if route[0].action != RouteAction.DEPOT_START or route[-1].action != RouteAction.DEPOT_END:
                violations.append(Violation("DEPOT", "Route must start and end at the depot"))
            seen_return = False
            for item in route:
                if item.action in (RouteAction.PICKUP, RouteAction.RETURN):
                    seen_return = True
                if seen_return and item.action == RouteAction.DELIVER:
                    violations.append(Violation("PRECEDENCE", "Delivery appears after return collection", item.external_id))
                if item.load_after_kg > vehicle.capacity_kg + 1e-6:
                    violations.append(Violation("CAPACITY", "Vehicle weight capacity exceeded", item.external_id, amount_kg=round(item.load_after_kg - vehicle.capacity_kg, 3)))
                if item.load_after_l > vehicle.capacity_l + 1e-6:
                    violations.append(Violation("CAPACITY", "Vehicle volume capacity exceeded", item.external_id, amount_l=round(item.load_after_l - vehicle.capacity_l, 3)))
                if item.stop:
                    window_end = datetime.combine(item.arrival_time.date(), item.stop.time_window_end)
                    if item.arrival_time > window_end:
                        violations.append(Violation("TIME_WINDOW", "Arrival is after the time window", item.external_id))
            hours = (route[-1].departure_time - route[0].arrival_time).total_seconds() / 3600
            if hours > self.settings.max_driver_hours:
                violations.append(Violation("DRIVER_HOURS", f"Route exceeds {self.settings.max_driver_hours:g} driver hours"))
        return ConstraintCheck(not violations, violations)

    @staticmethod
    def _routes_distance(routes: Sequence[Sequence[PlannedStop]]) -> float:
        return sum(item.distance_from_previous_km for route in routes for item in route)


class MetricsEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    def calculate(self, baseline: RoutePlan, optimized: RoutePlan, vehicles: Sequence[VehicleLike]) -> dict:
        before_distance = baseline.total_distance_km
        after_distance = optimized.total_distance_km
        efficiency = sum(vehicle.fuel_efficiency_km_per_l for vehicle in vehicles) / len(vehicles)
        hourly_cost = sum(vehicle.driver_hourly_cost for vehicle in vehicles) / len(vehicles)
        before_hours = sum((route[-1].departure_time - route[0].arrival_time).total_seconds() / 3600 for route in baseline.routes if route)
        after_hours = sum((route[-1].departure_time - route[0].arrival_time).total_seconds() / 3600 for route in optimized.routes if route)
        before_fuel, after_fuel = before_distance / efficiency, after_distance / efficiency
        pairs = {
            "fuel_litres": self._pair(before_fuel, after_fuel),
            "fuel_cost": self._pair(before_fuel * self.settings.fuel_price_per_litre, after_fuel * self.settings.fuel_price_per_litre),
            "co2_kg": self._pair(before_fuel * self.settings.co2_kg_per_litre, after_fuel * self.settings.co2_kg_per_litre),
            "driver_hours": self._pair(before_hours, after_hours),
            "labor_cost": self._pair(before_hours * hourly_cost, after_hours * hourly_cost),
        }
        pairs["total_cost"] = self._pair(pairs["fuel_cost"]["before"] + pairs["labor_cost"]["before"], pairs["fuel_cost"]["after"] + pairs["labor_cost"]["after"])
        saved = max(0.0, before_distance - after_distance)
        return {"distance": {"before_km": round(before_distance, 3), "after_km": round(after_distance, 3), "saved_km": round(saved, 3), "saved_percent": round(saved / before_distance * 100 if before_distance else 0.0, 2)}, **pairs}

    @staticmethod
    def _pair(before: float, after: float) -> dict[str, float]:
        saved = before - after
        return {"before": round(before, 3), "after": round(after, 3), "saved": round(saved, 3), "saved_percent": round(saved / before * 100 if before else 0.0, 2)}


class IncrementalOptimizer:
    def __init__(self, optimizer: RouteOptimizer):
        self.optimizer = optimizer

    def reoptimize(self, current_stops: Sequence[StopLike], vehicles: Sequence[VehicleLike], depot: Location, cancelled_stop_ids: set[str]) -> RoutePlan:
        remaining = [stop for stop in current_stops if stop.external_id not in cancelled_stop_ids]
        return self.optimizer.optimize(remaining, vehicles, depot)

    def repair(
        self,
        current_routes: Sequence[Sequence[PlannedStop]],
        current_stops: Sequence[StopLike],
        vehicles: Sequence[VehicleLike],
        depot: Location,
        removed_stop_ids: set[str],
        *,
        cluster_count: int,
    ) -> IncrementalRepair:
        """Repair existing vehicle order without reclustering or global 2-opt."""
        active = {
            stop.external_id: stop
            for stop in current_stops
            if stop.external_id not in removed_stop_ids
        }
        routes: list[list[PlannedStop]] = []
        assigned: set[str] = set()
        global_sequence = 0
        affected_vehicle: int | None = None
        previous_ids: list[str] = []
        updated_ids: list[str] = []
        changed_segment: list[str] = []

        for index, current_route in enumerate(current_routes):
            vehicle_sequence = index + 1
            old_ids = [
                self._external_id(item)
                for item in current_route
                if getattr(item, "stop", None) is not None
            ]
            new_ids = [external_id for external_id in old_ids if external_id in active]
            removed_here = [external_id for external_id in old_ids if external_id not in active]
            if removed_here and affected_vehicle is None:
                affected_vehicle = vehicle_sequence
                previous_ids = old_ids
                updated_ids = new_ids
                removed_index = old_ids.index(removed_here[0])
                changed_segment = old_ids[
                    max(0, removed_index - 1) : min(len(old_ids), removed_index + 2)
                ]
            ordered = [active[external_id] for external_id in new_ids]
            assigned.update(new_ids)
            materialized, global_sequence = self.optimizer._materialize(
                ordered,
                vehicles[min(index, len(vehicles) - 1)],
                depot,
                vehicle_sequence,
                global_sequence,
            )
            routes.append(materialized)

        unassigned = [
            stop for stop in current_stops if stop.external_id in active and stop.external_id not in assigned
        ]
        for stop in unassigned:
            route_index = min(
                range(len(routes)),
                key=lambda value: sum(1 for item in routes[value] if item.stop),
            )
            current_ids = [item.external_id for item in routes[route_index] if item.stop]
            insertion = len(current_ids)
            if stop.type == StopType.DELIVERY:
                insertion = next(
                    (
                        position
                        for position, external_id in enumerate(current_ids)
                        if active[external_id].type != StopType.DELIVERY
                    ),
                    len(current_ids),
                )
            current_ids.insert(insertion, stop.external_id)
            materialized, _ = self.optimizer._materialize(
                [active[external_id] for external_id in current_ids],
                vehicles[min(route_index, len(vehicles) - 1)],
                depot,
                route_index + 1,
                0,
            )
            routes[route_index] = materialized

        global_sequence = 0
        renumbered: list[list[PlannedStop]] = []
        for index, route in enumerate(routes):
            ordered = [item.stop for item in route if item.stop]
            materialized, global_sequence = self.optimizer._materialize(
                ordered,
                vehicles[min(index, len(vehicles) - 1)],
                depot,
                index + 1,
                global_sequence,
            )
            renumbered.append(materialized)

        plan = RoutePlan(
            routes=renumbered,
            cluster_count=cluster_count,
            total_distance_km=round(self.optimizer._routes_distance(renumbered), 3),
            constraints=self.optimizer.check_constraints(renumbered, vehicles, depot),
        )
        return IncrementalRepair(
            plan=plan,
            affected_vehicle_sequence=affected_vehicle,
            removed_stop_ids=sorted(removed_stop_ids),
            previous_stop_ids=previous_ids,
            updated_stop_ids=updated_ids,
            changed_segment_stop_ids=changed_segment,
        )

    @staticmethod
    def _external_id(item: object) -> str:
        direct = getattr(item, "external_id", None)
        if direct:
            return str(direct)
        stop = getattr(item, "stop", None)
        return str(stop.external_id)
