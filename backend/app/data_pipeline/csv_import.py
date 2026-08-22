from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from pydantic import ValidationError

from app.schemas import ImportErrorDetail, StopImportRow

REQUIRED_COLUMNS = {
    "stop_id",
    "type",
    "lat",
    "lng",
    "address",
    "weight_kg",
    "volume_l",
    "time_window_start",
    "time_window_end",
}
OPTIONAL_COLUMNS = {
    "service_time_seconds",
    "return_count_30d",
    "avg_delivery_confirm_minutes",
    "dispute_history_count",
    "data_provenance",
}


def parse_csv(content: bytes) -> tuple[list[StopImportRow], list[ImportErrorDetail]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return [], [ImportErrorDetail(row=0, field="file", error=f"must be UTF-8 encoded: {exc}")]

    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        return [], [ImportErrorDetail(row=1, field="file", error="CSV header is missing")]

    fields = {field.strip() for field in reader.fieldnames if field}
    missing = sorted(REQUIRED_COLUMNS - fields)
    if missing:
        return [], [ImportErrorDetail(row=1, field=field, error="required column is missing") for field in missing]

    rows: list[StopImportRow] = []
    errors: list[ImportErrorDetail] = []
    for row_number, raw in enumerate(reader, start=2):
        payload = _normalize_row(raw)
        try:
            rows.append(StopImportRow.model_validate(payload))
        except ValidationError as exc:
            for error in exc.errors():
                field = str(error["loc"][0]) if error["loc"] else "row"
                message = str(error["msg"]).removeprefix("Value error, ")
                errors.append(ImportErrorDetail(row=row_number, field=field, error=message))
    return rows, errors


def _normalize_row(raw: dict[str, str | None]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in raw.items():
        if key is None:
            continue
        field = key.strip()
        normalized = value.strip() if isinstance(value, str) else value
        if normalized == "" and field in OPTIONAL_COLUMNS:
            continue
        result[field] = normalized
    if "type" in result and isinstance(result["type"], str):
        result["type"] = result["type"].upper()
    return result
