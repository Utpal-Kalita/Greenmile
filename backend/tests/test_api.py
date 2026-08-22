from app.data_pipeline.seed import generate_delhi_stops
from app.db.models import Vehicle
from app.repositories.scenarios import ScenarioRepository
from app.schemas import ScenarioCreate


async def create_scenario(session, count=20):
    repository = ScenarioRepository(session)
    scenario = await repository.create(ScenarioCreate(name="Test route", city="Delhi", depot_lat=28.5355, depot_lng=77.2732, depot_address="Okhla", vehicle_count=2, vehicle_capacity_kg=320, vehicle_capacity_l=640))
    await repository.replace_stops(scenario, generate_delhi_stops(count=count))
    await repository.add_vehicles([Vehicle(scenario_id=scenario.id, vehicle_code=f"T-{index}", capacity_kg=320, capacity_l=640, fuel_type="DIESEL", fuel_efficiency_km_per_l=12, driver_hourly_cost=180) for index in range(2)])
    await session.commit()
    return scenario


async def test_health_and_scenario_crud(client):
    health = await client.get("/health/ready")
    assert health.status_code == 200
    response = await client.post("/api/scenarios", json={"name":"API scenario","city":"Delhi","depot_lat":28.53,"depot_lng":77.27,"depot_address":"Okhla","vehicle_count":1,"vehicle_capacity_kg":100,"vehicle_capacity_l":200})
    assert response.status_code == 201
    assert response.json()["stop_count"] == 0


async def test_scenario_map_endpoint_returns_backend_geojson(client, session):
    scenario = await create_scenario(session)

    response = await client.get(f"/api/scenarios/{scenario.id}/map")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_id"] == str(scenario.id)
    assert payload["stops"]["type"] == "FeatureCollection"
    assert len(payload["stops"]["features"]) == 20
    assert payload["warehouse"]["geometry"]["coordinates"] == [77.2732, 28.5355]
    assert payload["routes"]["baseline_delivery"]["features"]
    assert payload["routes"]["baseline_return"]["features"]
    assert payload["routes"]["optimized"]["features"] == []


async def test_complete_optimization_and_event(client, session):
    scenario = await create_scenario(session)
    created = await client.post("/api/optimization-runs", json={"scenario_id": str(scenario.id)})
    assert created.status_code == 202
    run_id = created.json()["id"]
    # BackgroundTasks execute within ASGITransport before the response returns.
    result = await client.get(f"/api/optimization-runs/{run_id}")
    payload = result.json()
    assert payload["status"] == "COMPLETED"
    assert payload["metrics"]["distance"]["after_km"] > 0
    assert payload["route"][0]["action"] == "DEPOT_START"
    assert payload["prediction"]["status"] == "UNAVAILABLE"
    target = next(item for item in payload["route"] if item["stop_id"])
    changed = await client.post(f"/api/optimization-runs/{run_id}/events", json={"event_type":"DELIVERY_FAILED","stop_id":target["stop_id"],"payload":{"reason":"CUSTOMER_UNAVAILABLE"}})
    assert changed.status_code == 200
    assert any(event["event_type"] == "ROUTE_UPDATED" for event in changed.json()["events"])


async def test_run_map_reflects_real_event_and_incremental_route(client, session):
    scenario = await create_scenario(session)
    created = await client.post(
        "/api/optimization-runs", json={"scenario_id": str(scenario.id)}
    )
    run_id = created.json()["id"]
    run = (await client.get(f"/api/optimization-runs/{run_id}")).json()

    initial_map = await client.get(f"/api/optimization-runs/{run_id}/map")

    assert initial_map.status_code == 200
    initial_payload = initial_map.json()
    assert initial_payload["routes"]["optimized"]["features"]
    assert initial_payload["performance"]["optimization_latency_ms"] > 0
    target = next(item for item in run["route"] if item["action"] == "DELIVER")
    original_coordinates = initial_payload["routes"]["optimized"]["features"]

    changed = await client.post(
        f"/api/optimization-runs/{run_id}/events",
        json={
            "event_type": "DELIVERY_FAILED",
            "stop_id": target["stop_id"],
            "payload": {"reason": "CUSTOMER_UNAVAILABLE"},
        },
    )
    assert changed.status_code == 200
    updated_map = (
        await client.get(f"/api/optimization-runs/{run_id}/map")
    ).json()

    assert updated_map["routes"]["optimized"]["features"] != original_coordinates
    assert updated_map["performance"]["reoptimization_latency_ms"] > 0
    assert any(
        event["properties"]["event_type"] == "DELIVERY_FAILED"
        for event in updated_map["events"]["features"]
    )
    assert all(
        target["external_id"] not in feature["properties"]["stop_ids"]
        for feature in updated_map["routes"]["optimized"]["features"]
    )

    second_target = next(
        item
        for item in changed.json()["route"]
        if item["action"] == "DELIVER" and item["stop_id"] != target["stop_id"]
    )
    changed_again = await client.post(
        f"/api/optimization-runs/{run_id}/events",
        json={
            "event_type": "DELIVERY_FAILED",
            "stop_id": second_target["stop_id"],
            "payload": {"reason": "ADDRESS_CLOSED"},
        },
    )
    assert changed_again.status_code == 200
    final_map = (await client.get(f"/api/optimization-runs/{run_id}/map")).json()
    final_stop_ids = {
        stop_id
        for feature in final_map["routes"]["optimized"]["features"]
        for stop_id in feature["properties"]["stop_ids"]
    }
    assert target["external_id"] not in final_stop_ids
    assert second_target["external_id"] not in final_stop_ids
