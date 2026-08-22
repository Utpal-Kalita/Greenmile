from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass
from datetime import time

from app.domain.enums import StopType
from app.optimizer.engine import Location

REQUIRED_WORKLOADS = (100, 500, 1_000, 2_500, 5_000)
DATASET_VERSION = "round2-delhi-v1"
_NAMESPACE = uuid.UUID("7b68b251-b707-4c16-9b6e-bad7e11e4202")


@dataclass(frozen=True)
class BenchmarkStop:
    id: uuid.UUID
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


@dataclass(frozen=True)
class BenchmarkVehicle:
    id: uuid.UUID
    vehicle_code: str
    capacity_kg: float
    capacity_l: float
    fuel_efficiency_km_per_l: float
    driver_hourly_cost: float


@dataclass(frozen=True)
class BenchmarkScenario:
    name: str
    version: str
    seed: int
    depot: Location
    stops: tuple[BenchmarkStop, ...]
    vehicles: tuple[BenchmarkVehicle, ...]


def generate_scenario(stop_count: int, *, seed: int = 20_260_823) -> BenchmarkScenario:
    """Create a stable, representative Delhi workload without database or network I/O."""
    if stop_count not in REQUIRED_WORKLOADS:
        raise ValueError(f"stop_count must be one of {REQUIRED_WORKLOADS}")
    rng = random.Random(seed + stop_count)
    depot = Location(28.6139, 77.2090)
    centers = (
        (28.6328, 77.2197),
        (28.5897, 77.2219),
        (28.6505, 77.1855),
        (28.5706, 77.1792),
        (28.6172, 77.2760),
        (28.6770, 77.2050),
        (28.5480, 77.2510),
        (28.6410, 77.1260),
    )
    stops: list[BenchmarkStop] = []
    for index in range(stop_count):
        center_lat, center_lng = centers[index % len(centers)]
        angle = rng.random() * math.tau
        radius = math.sqrt(rng.random()) * 0.018
        stop_type = StopType.RETURN if index % 5 == 4 else StopType.DELIVERY
        external_id = f"{'R' if stop_type == StopType.RETURN else 'D'}-{index + 1:05d}"
        stops.append(
            BenchmarkStop(
                id=uuid.uuid5(_NAMESPACE, f"{seed}:{stop_count}:{external_id}"),
                external_id=external_id,
                type=stop_type,
                address=f"Benchmark stop {index + 1}, Delhi",
                lat=round(center_lat + math.sin(angle) * radius, 7),
                lng=round(center_lng + math.cos(angle) * radius, 7),
                weight_kg=round(2.0 + rng.random() * 18.0, 3),
                volume_l=round(4.0 + rng.random() * 46.0, 3),
                time_window_start=time(8, 0),
                time_window_end=time(23, 59),
                service_time_seconds=60,
            )
        )
    vehicle_count = max(1, math.ceil(stop_count / 250))
    vehicles = tuple(
        BenchmarkVehicle(
            id=uuid.uuid5(_NAMESPACE, f"{seed}:{stop_count}:vehicle:{index}"),
            vehicle_code=f"BENCH-{index + 1:02d}",
            capacity_kg=5_000.0,
            capacity_l=15_000.0,
            fuel_efficiency_km_per_l=12.0,
            driver_hourly_cost=180.0,
        )
        for index in range(vehicle_count)
    )
    return BenchmarkScenario(
        name=f"delhi-{stop_count}",
        version=DATASET_VERSION,
        seed=seed,
        depot=depot,
        stops=tuple(stops),
        vehicles=vehicles,
    )
