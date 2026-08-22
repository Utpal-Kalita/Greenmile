from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import OptimizationRun, RouteStop, Scenario, TripEvent
from app.domain.enums import EventType, RunStatus


class OptimizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, scenario_id: uuid.UUID, algorithm_version: str, routing_provider: str, vehicle_id: uuid.UUID | None = None) -> OptimizationRun:
        run_uuid = uuid.uuid4()
        run = OptimizationRun(
            id=run_uuid,
            public_id=f"GM-{run_uuid.hex[:6].upper()}",
            scenario_id=scenario_id,
            vehicle_id=vehicle_id,
            status=RunStatus.QUEUED,
            system_state="OPTIMIZATION_RUNNING",
            algorithm_version=algorithm_version,
            routing_provider=routing_provider,
            started_at=datetime.now(UTC),
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def get(self, run_id: uuid.UUID | str, *, full: bool = False) -> OptimizationRun | None:
        condition = OptimizationRun.public_id == run_id if isinstance(run_id, str) else OptimizationRun.id == run_id
        statement = select(OptimizationRun).where(condition)
        if full:
            statement = statement.options(
                selectinload(OptimizationRun.scenario).selectinload(Scenario.stops),
                selectinload(OptimizationRun.scenario).selectinload(Scenario.vehicles),
                selectinload(OptimizationRun.vehicle),
                selectinload(OptimizationRun.route_stops).selectinload(RouteStop.stop),
                selectinload(OptimizationRun.events),
                selectinload(OptimizationRun.ai_analyses),
            ).execution_options(populate_existing=True)
        return await self.session.scalar(statement)

    async def latest_for_scenario(self, scenario_id: uuid.UUID) -> OptimizationRun | None:
        return await self.session.scalar(
            select(OptimizationRun)
            .where(OptimizationRun.scenario_id == scenario_id, OptimizationRun.status == RunStatus.COMPLETED)
            .order_by(OptimizationRun.created_at.desc())
            .limit(1)
        )

    async def replace_route(self, run: OptimizationRun, route_stops: list[RouteStop]) -> None:
        await self.session.execute(delete(RouteStop).where(RouteStop.optimization_run_id == run.id))
        self.session.add_all(route_stops)
        await self.session.flush()

    async def add_event(self, run: OptimizationRun, event_type: EventType, payload: dict, duration_ms: float | None = None, stop_id: uuid.UUID | None = None) -> TripEvent:
        event = TripEvent(optimization_run_id=run.id, stop_id=stop_id, event_type=event_type, payload=payload, duration_ms=duration_ms)
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_events(self, run_id: uuid.UUID, after: datetime | None = None) -> list[TripEvent]:
        statement = select(TripEvent).where(TripEvent.optimization_run_id == run_id)
        if after:
            statement = statement.where(TripEvent.created_at > after)
        result = await self.session.scalars(statement.order_by(TripEvent.created_at, TripEvent.id))
        return list(result)
