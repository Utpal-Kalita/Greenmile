from __future__ import annotations

import uuid
from datetime import UTC, datetime, time
from types import SimpleNamespace

from app.domain.enums import RouteAction, ScenarioStatus, StopStatus, StopType
from app.optimizer.engine import PlannedStop
from app.schemas import ScenarioRead, StageEventRead, StopRead
from app.services.map_data import MapDataService


def _scenario() -> ScenarioRead:
    now = datetime.now(UTC)
    return ScenarioRead(
        id=uuid.uuid4(),
        name="Delhi map",
        description="Map contract test",
        city="Delhi",
        status=ScenarioStatus.READY,
        depot_lat=28.5355,
        depot_lng=77.2732,
        depot_address="Okhla warehouse",
        vehicle_count=1,
        vehicle_capacity_kg=320,
        vehicle_capacity_l=640,
        provenance={"kind": "TEST"},
        is_demo=True,
        created_at=now,
        updated_at=now,
        stop_count=2,
        delivery_count=1,
        return_count=1,
    )


def _stop(external_id: str, stop_type: StopType, lat: float, lng: float) -> StopRead:
    return StopRead(
        id=uuid.uuid4(),
        scenario_id=uuid.uuid4(),
        external_id=external_id,
        type=stop_type,
        address=f"{external_id}, Delhi",
        lat=lat,
        lng=lng,
        weight_kg=2,
        volume_l=4,
        time_window_start=time(8),
        time_window_end=time(20),
        service_time_seconds=300,
        return_count_30d=2,
        avg_delivery_confirm_minutes=8,
        dispute_history_count=0,
        status=StopStatus.PENDING,
        data_provenance="TEST",
    )


def _planned(stop: StopRead, sequence: int, action: RouteAction) -> PlannedStop:
    now = datetime.now(UTC)
    return PlannedStop(
        stop=stop,
        external_id=stop.external_id,
        name=stop.external_id,
        address=stop.address,
        lat=stop.lat,
        lng=stop.lng,
        type=stop.type,
        action=action,
        vehicle_sequence=1,
        sequence_number=sequence,
        arrival_time=now,
        departure_time=now,
        load_before_kg=2,
        load_after_kg=0,
        load_before_l=4,
        load_after_l=0,
        distance_from_previous_km=1,
    )


def test_scenario_map_uses_real_stops_warehouse_and_separate_baselines():
    scenario = _scenario()
    delivery = _stop("D1", StopType.DELIVERY, 28.54, 77.28)
    returned = _stop("R1", StopType.RETURN, 28.55, 77.29)
    payload = MapDataService().build(
        scenario=scenario,
        stops=[delivery, returned],
        baseline_routes=[
            [_planned(delivery, 1, RouteAction.DELIVER)],
            [_planned(returned, 2, RouteAction.RETURN)],
        ],
    )

    assert payload.stops.type == "FeatureCollection"
    assert [feature.properties["stop_id"] for feature in payload.stops.features] == ["D1", "R1"]
    assert payload.warehouse.geometry["coordinates"] == [77.2732, 28.5355]
    assert len(payload.routes.baseline_delivery.features) == 1
    assert len(payload.routes.baseline_return.features) == 1
    assert payload.routes.optimized.features == []
    assert payload.map.bounds.west <= 77.2732 <= payload.map.bounds.east
    assert payload.map.bounds.south <= 28.5355 <= payload.map.bounds.north


def test_stage_event_exposes_stop_id_for_map_updates():
    stop_id = uuid.uuid4()
    event = StageEventRead.model_validate(
        SimpleNamespace(
            id=uuid.uuid4(),
            event_type="DELIVERY_FAILED",
            stop_id=stop_id,
            payload={"reason": "CUSTOMER_UNAVAILABLE"},
            duration_ms=12.5,
            created_at=datetime.now(UTC),
        )
    )

    assert event.stop_id == stop_id


def test_run_map_merges_predictions_events_and_all_vehicle_routes():
    scenario = _scenario()
    delivery = _stop("D1", StopType.DELIVERY, 28.54, 77.28)
    returned = _stop("R1", StopType.RETURN, 28.55, 77.29)
    first_route = _planned(delivery, 1, RouteAction.DELIVER)
    second_route = _planned(returned, 2, RouteAction.RETURN)
    second_route.vehicle_sequence = 2
    event = SimpleNamespace(
        id=uuid.uuid4(),
        event_type="DELIVERY_FAILED",
        stop_id=delivery.id,
        payload={"reason": "CUSTOMER_UNAVAILABLE"},
        duration_ms=18.4,
        created_at=datetime.now(UTC),
    )

    payload = MapDataService().build(
        scenario=scenario,
        stops=[delivery, returned],
        baseline_routes=[],
        optimized_route=[first_route, second_route],
        events=[event],
        predictions=[
            {
                "stop_id": "D1",
                "return_probability": 0.84,
                "risk": "HIGH",
                "recommended_action": "RESERVE_CAPACITY",
            }
        ],
        run_id="GM-TEST01",
        system_state="TRIP_CHANGED",
        optimization_latency_ms=842,
        reoptimization_latency_ms=18.4,
    )

    assert len(payload.routes.optimized.features) == 2
    assert payload.stops.features[0].properties["return_probability"] == 0.84
    assert payload.stops.features[0].properties["risk"] == "HIGH"
    assert payload.events.features[0].properties["event_type"] == "DELIVERY_FAILED"
    assert payload.events.features[0].geometry["coordinates"] == [77.28, 28.54]
    assert payload.performance.optimization_latency_ms == 842
    assert payload.performance.reoptimization_latency_ms == 18.4


def test_map_conversion_keeps_all_5000_stops():
    scenario = _scenario()
    stops = [
        _stop(
            f"D{index:04d}",
            StopType.DELIVERY if index % 2 == 0 else StopType.RETURN,
            28.50 + (index % 100) * 0.0001,
            77.20 + (index // 100) * 0.0001,
        )
        for index in range(5000)
    ]

    payload = MapDataService().build(
        scenario=scenario,
        stops=stops,
        baseline_routes=[],
    )

    assert len(payload.stops.features) == 5000
