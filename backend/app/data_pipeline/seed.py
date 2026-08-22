from __future__ import annotations

import argparse
import asyncio
import math
import random
from datetime import time

from app.core.config import get_settings
from app.db.models import Vehicle
from app.db.session import SessionFactory
from app.domain.enums import StopType
from app.repositories.scenarios import ScenarioRepository
from app.schemas import ScenarioCreate, StopImportRow

SEED_VERSION = "delhi-synthetic-v2"
NEIGHBORHOODS = [
    ("Okhla", 28.5355, 77.2732),
    ("Kalkaji", 28.5357, 77.2600),
    ("Nehru Place", 28.5494, 77.2501),
    ("Greater Kailash", 28.5357, 77.2410),
    ("Lajpat Nagar", 28.5677, 77.2433),
    ("Hauz Khas", 28.5494, 77.2001),
    ("Malviya Nagar", 28.5355, 77.2100),
    ("Saket", 28.5245, 77.2066),
    ("Vasant Kunj", 28.5200, 77.1590),
    ("Chittaranjan Park", 28.5388, 77.2492),
    ("Defence Colony", 28.5734, 77.2326),
    ("Green Park", 28.5580, 77.2026),
]


def generate_delhi_stops(count: int = 500, seed: int = 20260822) -> list[StopImportRow]:
    rng = random.Random(seed)
    rows: list[StopImportRow] = []
    for index in range(count):
        name, center_lat, center_lng = NEIGHBORHOODS[index % len(NEIGHBORHOODS)]
        angle = (index * 137.508) * math.pi / 180
        radius = 0.002 + (index % 17) * 0.00042
        lat = center_lat + math.cos(angle) * radius + rng.uniform(-0.00035, 0.00035)
        lng = center_lng + math.sin(angle) * radius + rng.uniform(-0.00035, 0.00035)
        kind = StopType.DELIVERY if index % 2 == 0 else StopType.RETURN
        start_hour = 8
        rows.append(
            StopImportRow(
                stop_id=f"{'D' if kind == StopType.DELIVERY else 'R'}{index // 2 + 1:03d}",
                type=kind,
                lat=round(lat, 6),
                lng=round(lng, 6),
                address=f"Block {chr(65 + index % 12)}-{index % 97 + 1}, {name}, New Delhi",
                weight_kg=round(0.35 + (index * 17 % 390) / 100, 2),
                volume_l=round(0.8 + (index * 23 % 820) / 100, 2),
                time_window_start=time(start_hour, 0),
                time_window_end=time(20, 0),
                service_time_seconds=45 + (index % 4) * 15,
                return_count_30d=(index * 3) % 8,
                avg_delivery_confirm_minutes=round(3 + (index * 11 % 160) / 10, 1),
                dispute_history_count=index % 4,
                data_provenance="SYNTHETIC_DETERMINISTIC",
            )
        )
    return rows


async def seed_demo(force: bool = False) -> str:
    settings = get_settings()
    async with SessionFactory() as session:
        repository = ScenarioRepository(session)
        existing = await repository.get_demo()
        is_current = bool(existing and existing.provenance.get("generator") == SEED_VERSION)
        if existing and not force and is_current:
            return str(existing.id)
        if existing:
            await session.delete(existing)
            await session.flush()

        scenario = await repository.create(
            ScenarioCreate(
                name="Delhi NCR — Zone B",
                description="Deterministic synthetic reverse-logistics workload for reproducible demonstrations and benchmarks.",
                city="New Delhi",
                depot_lat=28.5355,
                depot_lng=77.2732,
                depot_address="Okhla Industrial Estate, New Delhi",
                vehicle_count=5,
                vehicle_capacity_kg=320.0,
                vehicle_capacity_l=640.0,
                provenance={
                    "kind": "SYNTHETIC_DETERMINISTIC",
                    "generator": SEED_VERSION,
                    "seed": 20260822,
                    "claims": "Not observed real-world fleet data",
                },
            ),
            is_demo=True,
        )
        await repository.replace_stops(scenario, generate_delhi_stops())
        vehicles = [
            Vehicle(
                scenario_id=scenario.id,
                vehicle_code=f"DL-01-GM-{4800 + number}",
                capacity_kg=scenario.vehicle_capacity_kg,
                capacity_l=scenario.vehicle_capacity_l,
                fuel_type="DIESEL",
                fuel_efficiency_km_per_l=settings.vehicle_fuel_efficiency_km_per_l,
                driver_hourly_cost=settings.driver_cost_per_hour,
            )
            for number in range(1, scenario.vehicle_count + 1)
        ]
        await repository.add_vehicles(vehicles)
        await session.commit()
        return str(scenario.id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the deterministic Greenmile demo scenario")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(asyncio.run(seed_demo(force=args.force)))
