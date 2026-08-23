from sqlalchemy import func, select

from app.data_pipeline.csv_import import parse_csv
from app.data_pipeline.seed import generate_delhi_stops, seed_demo
from app.db.models import Scenario, Stop, Vehicle


def test_seed_is_deterministic_and_balanced():
    first = generate_delhi_stops()
    second = generate_delhi_stops()
    assert len(first) == 500
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]
    assert sum(item.type.value == "DELIVERY" for item in first) == 250
    assert all(item.data_provenance == "SYNTHETIC_DETERMINISTIC" for item in first)


async def test_seed_demo_is_idempotent(session, test_session_factory):
    first_id = await seed_demo(session_factory=test_session_factory)
    second_id = await seed_demo(session_factory=test_session_factory)

    assert second_id == first_id
    assert await session.scalar(select(func.count(Scenario.id))) == 1
    assert await session.scalar(select(func.count(Stop.id))) == 500
    assert await session.scalar(select(func.count(Vehicle.id))) == 5


def test_csv_returns_structured_validation_errors():
    rows, errors = parse_csv(
        b"stop_id,type,lat,lng,address,weight_kg,volume_l,time_window_start,time_window_end\n"
        b"D1,DELIVERY,91,77.1,Delhi,-2,4,12:00,10:00\n"
    )
    assert rows == []
    assert {error.field for error in errors} >= {"lat", "weight_kg"}
    assert all(error.row == 2 for error in errors)


def test_csv_rejects_missing_columns():
    rows, errors = parse_csv(b"stop_id,type\nD1,DELIVERY\n")
    assert rows == []
    assert any(error.field == "lat" for error in errors)
