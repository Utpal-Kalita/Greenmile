from dataclasses import dataclass
from datetime import time
import uuid

from app.core.config import Settings
from app.domain.enums import RouteAction, StopType
from app.optimizer.engine import HaversineProvider, IncrementalOptimizer, Location, MetricsEngine, RouteOptimizer


@dataclass
class StubStop:
    external_id: str
    type: StopType
    lat: float
    lng: float
    weight_kg: float = 2
    volume_l: float = 4
    address: str = "Block A, Delhi"
    time_window_start: time = time(8)
    time_window_end: time = time(20)
    service_time_seconds: int = 60
    id: uuid.UUID = uuid.uuid4()


@dataclass
class StubVehicle:
    vehicle_code: str = "GM-001"
    capacity_kg: float = 100
    capacity_l: float = 200
    fuel_efficiency_km_per_l: float = 12
    driver_hourly_cost: float = 180
    id: uuid.UUID = uuid.uuid4()


def test_optimizer_is_deterministic_and_closes_route():
    settings = Settings(two_opt_max_iterations=10)
    optimizer = RouteOptimizer(HaversineProvider(), settings)
    stops = [StubStop("D1", StopType.DELIVERY, 28.53, 77.21), StubStop("R1", StopType.RETURN, 28.55, 77.23), StubStop("D2", StopType.DELIVERY, 28.54, 77.20)]
    depot = Location(28.5355, 77.2732)
    first = optimizer.optimize(stops, [StubVehicle()], depot)
    second = optimizer.optimize(stops, [StubVehicle()], depot)
    assert [item.external_id for item in first.stops] == [item.external_id for item in second.stops]
    assert first.stops[0].action == RouteAction.DEPOT_START
    assert first.stops[-1].action == RouteAction.DEPOT_END
    actions = [item.action for item in first.stops]
    assert max(index for index, action in enumerate(actions) if action == RouteAction.DELIVER) < min(index for index, action in enumerate(actions) if action == RouteAction.RETURN)


def test_metrics_are_derived_from_routes():
    settings = Settings(two_opt_max_iterations=10)
    optimizer = RouteOptimizer(HaversineProvider(), settings)
    stops = [StubStop(f"D{i}", StopType.DELIVERY, 28.53 + i * .01, 77.21) for i in range(4)] + [StubStop(f"R{i}", StopType.RETURN, 28.54, 77.20 + i * .01) for i in range(4)]
    vehicle = StubVehicle()
    depot = Location(28.5355, 77.2732)
    baseline = optimizer.baseline(stops, [vehicle], depot)
    optimized = optimizer.optimize(stops, [vehicle], depot)
    metrics = MetricsEngine(settings).calculate(baseline, optimized, [vehicle])
    assert metrics["distance"]["before_km"] == baseline.total_distance_km
    assert metrics["distance"]["after_km"] == optimized.total_distance_km
    assert metrics["fuel_cost"]["before"] > 0


def test_incremental_optimizer_removes_cancelled_stop():
    optimizer = RouteOptimizer(HaversineProvider(), Settings())
    stops = [StubStop("D1", StopType.DELIVERY, 28.53, 77.21), StubStop("R1", StopType.RETURN, 28.55, 77.23)]
    repaired = IncrementalOptimizer(optimizer).reoptimize(stops, [StubVehicle()], Location(28.5355, 77.2732), {"D1"})
    assert "D1" not in [item.external_id for item in repaired.stops]
    assert "R1" in [item.external_id for item in repaired.stops]


def test_incremental_repair_preserves_unaffected_vehicle_order(monkeypatch):
    optimizer = RouteOptimizer(HaversineProvider(), Settings())
    vehicles = [StubVehicle(vehicle_code="GM-001"), StubVehicle(vehicle_code="GM-002")]
    stops = [
        StubStop(f"D{index}", StopType.DELIVERY, 28.53 + index * 0.002, 77.21)
        for index in range(4)
    ] + [
        StubStop(f"R{index}", StopType.RETURN, 28.54, 77.22 + index * 0.002)
        for index in range(2)
    ]
    depot = Location(28.5355, 77.2732)
    current = optimizer.optimize(stops, vehicles, depot)
    target = next(item.external_id for item in current.routes[0] if item.stop)
    unaffected_before = [
        item.external_id for item in current.routes[1] if item.stop
    ]

    monkeypatch.setattr(
        optimizer,
        "optimize",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("full optimize must not run during local repair")
        ),
    )
    repair = IncrementalOptimizer(optimizer).repair(
        current.routes,
        stops,
        vehicles,
        depot,
        {target},
        cluster_count=current.cluster_count,
    )

    assert target not in [item.external_id for item in repair.plan.stops]
    assert [item.external_id for item in repair.plan.routes[1] if item.stop] == unaffected_before
    assert repair.affected_vehicle_sequence == 1
    assert repair.removed_stop_ids == [target]
