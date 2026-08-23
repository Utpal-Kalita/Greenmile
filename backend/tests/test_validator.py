import math
from dataclasses import replace
from datetime import time

from app.core.config import Settings
from app.domain.enums import RouteAction, StopType
from app.optimizer.engine import HaversineProvider, Location, MetricsEngine, RouteOptimizer
from app.optimizer.validator import RouteValidator
from tests.test_optimizer import StubStop, StubVehicle


def _build(stops=None, vehicles=None):
    stops = stops or [
        StubStop("D1", StopType.DELIVERY, 28.53, 77.21),
        StubStop("R1", StopType.RETURN, 28.55, 77.23),
        StubStop("D2", StopType.DELIVERY, 28.54, 77.20),
    ]
    vehicles = vehicles or [StubVehicle()]
    depot = Location(28.5355, 77.2732)
    optimizer = RouteOptimizer(HaversineProvider(), Settings(two_opt_max_iterations=10))
    plan = optimizer.optimize(stops, vehicles, depot)
    metrics = MetricsEngine(Settings()).calculate(optimizer.baseline(stops, vehicles, depot), plan, vehicles)
    return optimizer, stops, vehicles, depot, plan, metrics


def _types(result):
    return {violation.type for violation in result.violations}


def test_validator_accepts_complete_feasible_route():
    optimizer, stops, vehicles, depot, plan, metrics = _build()

    result = RouteValidator(optimizer.provider).validate(
        stops, plan.routes, vehicles, depot,
        total_distance_km=plan.total_distance_km,
        metrics=metrics,
    )

    assert result.feasible
    assert result.violations == []


def test_validator_reports_duplicate_missing_and_foreign_stops():
    optimizer, stops, vehicles, depot, plan, metrics = _build()
    route = plan.routes[0]
    first_stop = next(item for item in route if item.stop)
    route.insert(-1, replace(first_stop, sequence_number=999))
    removed = next(item for item in route if item.external_id == "D2")
    route.remove(removed)
    foreign = replace(first_stop, external_id="UNKNOWN", sequence_number=1000)
    route.insert(-1, foreign)

    result = RouteValidator(optimizer.provider).validate(
        stops, plan.routes, vehicles, depot,
        total_distance_km=plan.total_distance_km,
        metrics=metrics,
    )

    assert {"DUPLICATE_STOP", "MISSING_STOP", "FOREIGN_STOP"} <= _types(result)


def test_validator_reports_weight_and_volume_capacity():
    vehicle = StubVehicle(capacity_kg=3, capacity_l=5)
    _, _, _, _, plan, _ = _build(vehicles=[vehicle])

    assert not plan.constraints.feasible
    assert any(item.amount_kg for item in plan.constraints.violations if item.type == "CAPACITY_WEIGHT")
    assert any(item.amount_l for item in plan.constraints.violations if item.type == "CAPACITY_VOLUME")


def test_validator_reports_time_window_and_invalid_coordinates():
    late = StubStop("D1", StopType.DELIVERY, 28.53, 77.21, time_window_end=time(7, 59))
    invalid = StubStop("R1", StopType.RETURN, math.nan, 77.23)
    optimizer, stops, vehicles, depot, plan, _ = _build(stops=[late])
    required = [*stops, invalid]

    result = RouteValidator(optimizer.provider).validate(required, plan.routes, vehicles, depot)

    assert {"TIME_WINDOW", "INVALID_COORDINATE"} <= _types(result)


def test_validator_reports_bad_depot_and_distance_metric():
    optimizer, stops, vehicles, depot, plan, metrics = _build()
    plan.routes[0][0] = replace(plan.routes[0][0], action=RouteAction.DEPOT_END, lat=0)
    plan.routes[0][1] = replace(plan.routes[0][1], distance_from_previous_km=plan.routes[0][1].distance_from_previous_km + 1)
    metrics["distance"]["after_km"] += 1

    result = RouteValidator(optimizer.provider).validate(
        stops, plan.routes, vehicles, depot,
        total_distance_km=plan.total_distance_km,
        metrics=metrics,
    )

    assert {"DEPOT", "DISTANCE_TOTAL", "METRICS_DISTANCE"} <= _types(result)


def test_validator_reports_non_finite_route_values():
    optimizer, stops, vehicles, depot, plan, metrics = _build()
    plan.routes[0][1] = replace(plan.routes[0][1], distance_from_previous_km=math.inf)

    result = RouteValidator(optimizer.provider).validate(
        stops, plan.routes, vehicles, depot,
        total_distance_km=plan.total_distance_km,
        metrics=metrics,
    )

    assert "NON_FINITE" in _types(result)
