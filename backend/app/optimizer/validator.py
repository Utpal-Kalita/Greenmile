from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from math import isclose, isfinite
from typing import Any, Protocol

from app.domain.enums import RouteAction, StopType


class LocationLike(Protocol):
    lat: float
    lng: float


class StopLike(LocationLike, Protocol):
    external_id: str
    type: StopType
    weight_kg: float
    volume_l: float
    time_window_end: Any


class VehicleLike(Protocol):
    capacity_kg: float
    capacity_l: float


class PlannedStopLike(LocationLike, Protocol):
    stop: StopLike | None
    external_id: str
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


class DistanceProvider(Protocol):
    def distance(self, first: LocationLike, second: LocationLike) -> float: ...


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


class RouteValidator:
    """Validate route completeness, feasibility, and metric consistency."""

    _TOLERANCE = 1e-6
    _DISTANCE_TOLERANCE_KM = 0.002

    def __init__(self, provider: DistanceProvider):
        self.provider = provider

    def validate(
        self,
        required_stops: Sequence[StopLike],
        routes: Sequence[Sequence[PlannedStopLike]],
        vehicles: Sequence[VehicleLike],
        depot: LocationLike,
        *,
        total_distance_km: float | None = None,
        metrics: Mapping[str, Any] | None = None,
    ) -> ConstraintCheck:
        violations: list[Violation] = []
        required = {stop.external_id: stop for stop in required_stops}
        required_counts = Counter(stop.external_id for stop in required_stops)
        for external_id, count in required_counts.items():
            if count > 1:
                violations.append(Violation("DUPLICATE_INPUT", "Required stop id is duplicated", external_id))
            if not self._valid_coordinate(required[external_id]):
                violations.append(Violation("INVALID_COORDINATE", "Stop coordinates must be finite and in range", external_id))

        if not self._valid_coordinate(depot):
            violations.append(Violation("INVALID_DEPOT", "Depot coordinates must be finite and in range", "DEPOT"))
        if required_stops and not vehicles:
            violations.append(Violation("INPUT", "At least one vehicle is required"))

        visited: list[str] = []
        vehicle_by_sequence: dict[int, VehicleLike] = {}
        for route in routes:
            if not route:
                continue
            vehicle_sequence = route[0].vehicle_sequence
            if vehicles and vehicle_sequence not in vehicle_by_sequence:
                vehicle_by_sequence[vehicle_sequence] = vehicles[
                    min(len(vehicle_by_sequence), len(vehicles) - 1)
                ]
            self._validate_route(
                route,
                vehicle_by_sequence.get(vehicle_sequence),
                depot,
                required,
                violations,
            )
            visited.extend(item.external_id for item in route if item.stop is not None)

        visited_counts = Counter(visited)
        for external_id in sorted(required):
            count = visited_counts.get(external_id, 0)
            if count == 0:
                violations.append(Violation("MISSING_STOP", "Required stop is missing from route", external_id))
            elif count > 1:
                violations.append(Violation("DUPLICATE_STOP", "Stop appears more than once in route", external_id))
        for external_id in sorted(set(visited) - set(required)):
            violations.append(Violation("FOREIGN_STOP", "Route contains a stop not present in the required input", external_id))

        calculated_distance = sum(item.distance_from_previous_km for route in routes for item in route)
        if not isfinite(calculated_distance):
            violations.append(Violation("NON_FINITE", "Route distance contains a non-finite value"))
        if total_distance_km is not None:
            if not isfinite(total_distance_km):
                violations.append(Violation("NON_FINITE", "Total route distance must be finite"))
            elif isfinite(calculated_distance) and not isclose(
                calculated_distance,
                total_distance_km,
                abs_tol=self._DISTANCE_TOLERANCE_KM,
            ):
                violations.append(Violation("DISTANCE_TOTAL", "Stored route distance does not match route legs"))

        if metrics is not None:
            self._validate_metrics(metrics, total_distance_km, violations)
        return ConstraintCheck(not violations, violations)

    def _validate_route(
        self,
        route: Sequence[PlannedStopLike],
        vehicle: VehicleLike | None,
        depot: LocationLike,
        required: Mapping[str, StopLike],
        violations: list[Violation],
    ) -> None:
        first, last = route[0], route[-1]
        if (
            first.action != RouteAction.DEPOT_START
            or last.action != RouteAction.DEPOT_END
            or not self._same_location(first, depot)
            or not self._same_location(last, depot)
        ):
            violations.append(Violation("DEPOT", "Route must start and end at the configured depot"))

        seen_return = False
        previous_sequence: int | None = None
        previous: LocationLike = depot
        previous_item: PlannedStopLike | None = None
        for item in route:
            stop_id = item.external_id if item.stop is not None else None
            numeric_values = (
                item.lat,
                item.lng,
                item.load_before_kg,
                item.load_after_kg,
                item.load_before_l,
                item.load_after_l,
                item.distance_from_previous_km,
            )
            if not all(isfinite(value) for value in numeric_values):
                violations.append(Violation("NON_FINITE", "Route values must be finite", stop_id))
            if previous_sequence is not None and item.sequence_number <= previous_sequence:
                violations.append(Violation("SEQUENCE", "Route sequence numbers must increase", stop_id))
            previous_sequence = item.sequence_number
            if item.departure_time < item.arrival_time:
                violations.append(Violation("TIME_ORDER", "Departure cannot precede arrival", stop_id))
            if previous_item is not None and item.arrival_time < previous_item.departure_time:
                violations.append(Violation("TIME_ORDER", "Arrival cannot precede the prior departure", stop_id))
            if item.action in (RouteAction.PICKUP, RouteAction.RETURN):
                seen_return = True
            if seen_return and item.action == RouteAction.DELIVER:
                violations.append(Violation("PRECEDENCE", "Delivery appears after return collection", stop_id))

            if vehicle is not None:
                if item.load_before_kg > vehicle.capacity_kg + self._TOLERANCE or item.load_after_kg > vehicle.capacity_kg + self._TOLERANCE:
                    excess = max(item.load_before_kg, item.load_after_kg) - vehicle.capacity_kg
                    violations.append(Violation("CAPACITY_WEIGHT", "Vehicle weight capacity exceeded", stop_id, amount_kg=round(excess, 3)))
                if item.load_before_l > vehicle.capacity_l + self._TOLERANCE or item.load_after_l > vehicle.capacity_l + self._TOLERANCE:
                    excess = max(item.load_before_l, item.load_after_l) - vehicle.capacity_l
                    violations.append(Violation("CAPACITY_VOLUME", "Vehicle volume capacity exceeded", stop_id, amount_l=round(excess, 3)))
            if min(item.load_before_kg, item.load_after_kg, item.load_before_l, item.load_after_l) < -self._TOLERANCE:
                violations.append(Violation("NEGATIVE_LOAD", "Vehicle load cannot be negative", stop_id))

            if item.stop is not None:
                expected = required.get(item.external_id)
                if expected is not None:
                    window_end = datetime.combine(item.arrival_time.date(), expected.time_window_end)
                    if item.arrival_time > window_end:
                        violations.append(Violation("TIME_WINDOW", "Arrival is after the time window", item.external_id))
                    expected_delta_kg = -expected.weight_kg if expected.type == StopType.DELIVERY else expected.weight_kg
                    expected_delta_l = -expected.volume_l if expected.type == StopType.DELIVERY else expected.volume_l
                    if not isclose(item.load_after_kg - item.load_before_kg, expected_delta_kg, abs_tol=self._TOLERANCE):
                        violations.append(Violation("LOAD_TRANSITION", "Weight load change does not match stop demand", item.external_id))
                    if not isclose(item.load_after_l - item.load_before_l, expected_delta_l, abs_tol=self._TOLERANCE):
                        violations.append(Violation("LOAD_TRANSITION", "Volume load change does not match stop demand", item.external_id))
                if not self._valid_coordinate(item):
                    violations.append(Violation("INVALID_COORDINATE", "Route stop coordinates must be finite and in range", item.external_id))

            if previous_item is not None:
                if not isclose(previous_item.load_after_kg, item.load_before_kg, abs_tol=self._TOLERANCE):
                    violations.append(Violation("LOAD_CONTINUITY", "Weight load is discontinuous between stops", stop_id))
                if not isclose(previous_item.load_after_l, item.load_before_l, abs_tol=self._TOLERANCE):
                    violations.append(Violation("LOAD_CONTINUITY", "Volume load is discontinuous between stops", stop_id))

            if self._valid_coordinate(previous) and self._valid_coordinate(item):
                expected_distance = self.provider.distance(previous, item)
                if not isclose(expected_distance, item.distance_from_previous_km, abs_tol=self._DISTANCE_TOLERANCE_KM):
                    violations.append(Violation("LEG_DISTANCE", "Route leg distance does not match coordinates", stop_id))
            previous = item
            previous_item = item

    @staticmethod
    def _validate_metrics(
        metrics: Mapping[str, Any],
        total_distance_km: float | None,
        violations: list[Violation],
    ) -> None:
        def values(value: Any):
            if isinstance(value, Mapping):
                for child in value.values():
                    yield from values(child)
            elif isinstance(value, int | float) and not isinstance(value, bool):
                yield float(value)

        if not all(isfinite(value) for value in values(metrics)):
            violations.append(Violation("NON_FINITE_METRICS", "Metrics must contain only finite numbers"))
        distance = metrics.get("distance")
        after = distance.get("after_km") if isinstance(distance, Mapping) else None
        if total_distance_km is not None and isinstance(after, int | float) and not isclose(float(after), total_distance_km, abs_tol=0.002):
            violations.append(Violation("METRICS_DISTANCE", "Metrics distance does not match validated route distance"))

    @staticmethod
    def _valid_coordinate(value: LocationLike) -> bool:
        return isfinite(value.lat) and isfinite(value.lng) and -90 <= value.lat <= 90 and -180 <= value.lng <= 180

    @staticmethod
    def _same_location(first: LocationLike, second: LocationLike) -> bool:
        return isclose(first.lat, second.lat, abs_tol=1e-7) and isclose(first.lng, second.lng, abs_tol=1e-7)
