from __future__ import annotations

import asyncio
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.data_pipeline.csv_import import parse_csv
from app.db.models import Scenario, Vehicle
from app.optimizer.engine import HaversineProvider, Location, RouteOptimizer
from app.repositories.scenarios import ScenarioRepository
from app.schemas import ImportResult, MapPayload, ScenarioCreate, ScenarioRead, StopRead as StopResponse
from app.services.map_data import MapDataService


class ScenarioService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ScenarioRepository(session)

    async def list(self) -> list[ScenarioRead]:
        scenarios = await self.repository.list()
        return [await self._serialize(item) for item in scenarios]

    async def get(self, scenario_id: uuid.UUID) -> ScenarioRead:
        scenario = await self._required(scenario_id)
        return await self._serialize(scenario)

    async def get_demo(self) -> ScenarioRead:
        scenario = await self.repository.get_demo()
        if not scenario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo scenario is not seeded")
        return await self._serialize(scenario)

    async def get_demo_record(self) -> Scenario:
        scenario = await self.repository.get_demo()
        if not scenario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo scenario is not seeded")
        return scenario

    async def create(self, payload: ScenarioCreate) -> ScenarioRead:
        settings = get_settings()
        scenario = await self.repository.create(payload)
        vehicles = [
            Vehicle(
                scenario_id=scenario.id,
                vehicle_code=f"GM-{index + 1:03d}",
                capacity_kg=payload.vehicle_capacity_kg,
                capacity_l=payload.vehicle_capacity_l,
                fuel_type="DIESEL",
                fuel_efficiency_km_per_l=settings.vehicle_fuel_efficiency_km_per_l,
                driver_hourly_cost=settings.driver_cost_per_hour,
            )
            for index in range(payload.vehicle_count)
        ]
        await self.repository.add_vehicles(vehicles)
        await self.session.commit()
        return await self._serialize(scenario)

    async def stops(self, scenario_id: uuid.UUID) -> list[StopResponse]:
        await self._required(scenario_id)
        return [StopResponse.model_validate(stop) for stop in await self.repository.list_stops(scenario_id)]

    async def map_data(self, scenario_id: uuid.UUID) -> MapPayload:
        scenario = await self._required(scenario_id)
        settings = get_settings()
        baseline = await asyncio.to_thread(
            RouteOptimizer(HaversineProvider(), settings).baseline,
            scenario.stops,
            scenario.vehicles,
            Location(scenario.depot_lat, scenario.depot_lng),
        )
        return MapDataService().build(
            scenario=await self._serialize(scenario),
            stops=[StopResponse.model_validate(stop) for stop in scenario.stops],
            baseline_routes=baseline.routes,
        )

    async def import_stops(self, scenario_id: uuid.UUID, upload: UploadFile) -> ImportResult:
        scenario = await self._required(scenario_id)
        if not upload.filename or not upload.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="A .csv file is required")
        content = await upload.read()
        rows, errors = parse_csv(content)
        if errors:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=[error.model_dump() for error in errors])
        if not rows:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="CSV contains no data rows")
        await self.repository.replace_stops(scenario, rows)
        scenario.provenance = {"kind": "CSV_IMPORT", "filename": upload.filename, "row_count": len(rows)}
        await self.session.commit()
        return ImportResult(scenario_id=scenario.id, imported=len(rows), rejected=0)

    async def _required(self, scenario_id: uuid.UUID) -> Scenario:
        scenario = await self.repository.get(scenario_id, include_children=True)
        if not scenario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
        return scenario

    async def _serialize(self, scenario: Scenario) -> ScenarioRead:
        total, deliveries, returns = await self.repository.counts(scenario.id)
        return ScenarioRead.model_validate(scenario).model_copy(update={"stop_count": total, "delivery_count": deliveries, "return_count": returns})
