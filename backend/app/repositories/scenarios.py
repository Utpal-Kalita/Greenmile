from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Scenario, Stop, Vehicle
from app.domain.enums import ScenarioStatus
from app.schemas import ScenarioCreate, StopImportRow


class ScenarioRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> list[Scenario]:
        result = await self.session.scalars(select(Scenario).order_by(Scenario.created_at.desc()))
        return list(result)

    async def get(self, scenario_id: uuid.UUID, *, include_children: bool = False) -> Scenario | None:
        statement = select(Scenario).where(Scenario.id == scenario_id)
        if include_children:
            statement = statement.options(selectinload(Scenario.stops), selectinload(Scenario.vehicles))
        return await self.session.scalar(statement)

    async def get_demo(self) -> Scenario | None:
        return await self.session.scalar(
            select(Scenario)
            .where(Scenario.is_demo.is_(True))
            .options(selectinload(Scenario.stops), selectinload(Scenario.vehicles))
            .order_by(Scenario.created_at.desc())
        )

    async def create(self, payload: ScenarioCreate, *, is_demo: bool = False) -> Scenario:
        scenario = Scenario(**payload.model_dump(), is_demo=is_demo)
        self.session.add(scenario)
        await self.session.flush()
        return scenario

    async def replace_stops(self, scenario: Scenario, rows: list[StopImportRow]) -> list[Stop]:
        existing = await self.session.scalars(select(Stop).where(Stop.scenario_id == scenario.id))
        for stop in existing:
            await self.session.delete(stop)
        await self.session.flush()
        stops = [
            Stop(
                scenario_id=scenario.id,
                external_id=row.stop_id,
                **row.model_dump(exclude={"stop_id"}),
            )
            for row in rows
        ]
        self.session.add_all(stops)
        scenario.status = ScenarioStatus.READY
        await self.session.flush()
        return stops

    async def list_stops(self, scenario_id: uuid.UUID) -> list[Stop]:
        result = await self.session.scalars(
            select(Stop).where(Stop.scenario_id == scenario_id).order_by(Stop.external_id)
        )
        return list(result)

    async def add_vehicles(self, vehicles: list[Vehicle]) -> None:
        self.session.add_all(vehicles)
        await self.session.flush()

    async def counts(self, scenario_id: uuid.UUID) -> tuple[int, int, int]:
        rows = await self.session.execute(
            select(Stop.type, func.count(Stop.id)).where(Stop.scenario_id == scenario_id).group_by(Stop.type)
        )
        counts = {kind.value: count for kind, count in rows}
        return sum(counts.values()), counts.get("DELIVERY", 0), counts.get("RETURN", 0) + counts.get("PICKUP", 0)
