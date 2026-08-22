from app.data_pipeline.csv_import import parse_csv
from app.data_pipeline.seed import generate_delhi_stops


def test_seed_is_deterministic_and_balanced():
    first = generate_delhi_stops()
    second = generate_delhi_stops()
    assert len(first) == 500
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]
    assert sum(item.type.value == "DELIVERY" for item in first) == 250
    assert all(item.data_provenance == "SYNTHETIC_DETERMINISTIC" for item in first)


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
