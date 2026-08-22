from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import DatabaseSession
from app.db.session import SessionFactory
from app.domain.enums import EventType, RunStatus
from app.repositories.runs import OptimizationRepository
from app.schemas import MapPayload, OptimizationCreate, OptimizationRunRead, RouteStopRead, StageEventRead, TripEventCreate
from app.services.events import broker
from app.services.optimization import OptimizationService

router = APIRouter(prefix="/optimization-runs", tags=["optimization"])


async def execute_run(run_id: uuid.UUID) -> None:
    async with SessionFactory() as session:
        await OptimizationService(session).execute(run_id)
        completed = await OptimizationRepository(session).get(run_id)
    if not completed or completed.status != RunStatus.COMPLETED:
        return
    from app.services.intelligence import analyze_run

    await analyze_run(run_id)


@router.post("", response_model=OptimizationRunRead, status_code=status.HTTP_202_ACCEPTED)
async def create_optimization_run(payload: OptimizationCreate, background_tasks: BackgroundTasks, session: DatabaseSession) -> OptimizationRunRead:
    service = OptimizationService(session)
    run = await service.create_run(payload.scenario_id, payload.vehicle_id)
    result = await service.get(run.id)
    background_tasks.add_task(execute_run, run.id)
    return result


@router.get("/{run_id}", response_model=OptimizationRunRead)
async def get_optimization_run(run_id: str, session: DatabaseSession) -> OptimizationRunRead:
    return await OptimizationService(session).get(_parse_run_id(run_id))


@router.get("/{run_id}/route", response_model=list[RouteStopRead])
async def get_optimization_route(run_id: str, session: DatabaseSession) -> list[RouteStopRead]:
    return (await OptimizationService(session).get(_parse_run_id(run_id))).route


@router.get("/{run_id}/map", response_model=MapPayload)
async def get_optimization_map(run_id: str, session: DatabaseSession) -> MapPayload:
    return await OptimizationService(session).map_data(_parse_run_id(run_id))


@router.get("/{run_id}/events", response_model=list[StageEventRead])
async def get_optimization_events(run_id: str, session: DatabaseSession) -> list[StageEventRead]:
    return (await OptimizationService(session).get(_parse_run_id(run_id))).events


@router.post("/{run_id}/events", response_model=OptimizationRunRead)
async def submit_trip_event(run_id: str, payload: TripEventCreate, session: DatabaseSession) -> OptimizationRunRead:
    repository = OptimizationRepository(session)
    run = await repository.get(_parse_run_id(run_id), full=True)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization run not found")
    if payload.event_type not in {
        EventType.DELIVERY_COMPLETED, EventType.DELIVERY_FAILED, EventType.RETURN_READY,
        EventType.RETURN_COLLECTED, EventType.RETURN_CANCELLED, EventType.STOP_CANCELLED,
        EventType.CAPACITY_CHANGED, EventType.TRAFFIC_DELAY, EventType.DRIVER_DELAY,
    }:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Event type is not a trip event")
    return await OptimizationService(session).adapt(run, payload.event_type, payload.stop_id, payload.payload)


@router.get("/{run_id}/events/stream")
async def stream_optimization_events(run_id: str, request: Request, session: DatabaseSession) -> StreamingResponse:
    repository = OptimizationRepository(session)
    run = await repository.get(_parse_run_id(run_id), full=True)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization run not found")
    historical = [StageEventRead.model_validate(item).model_dump(mode="json") for item in sorted(run.events, key=lambda value: value.created_at)]
    queue = broker.subscribe(run.id)

    async def stream():
        try:
            for event in historical:
                yield _sse(event)
            if run.status in {RunStatus.FAILED, RunStatus.CANCELLED}:
                return
            while not await request.is_disconnected():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield _sse(event)
        finally:
            broker.unsubscribe(run.id, queue)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _sse(event: dict) -> str:
    return f"id: {event['id']}\nevent: {event['event_type']}\ndata: {json.dumps(event, separators=(',', ':'))}\n\n"


def _parse_run_id(value: str) -> uuid.UUID | str:
    if value.upper().startswith("GM-"):
        return value.upper()
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid run id") from exc
