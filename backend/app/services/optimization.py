from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import logger
from app.db.models import OptimizationRun, RouteStop
from app.domain.enums import EventType, ProviderStatus, RouteAction, RunStatus, StopStatus
from app.optimizer.engine import HaversineProvider, IncrementalOptimizer, Location, MetricsEngine, RouteOptimizer
from app.providers.contracts import NoIntelligenceProvider, NoPredictionProvider
from app.repositories.runs import OptimizationRepository
from app.repositories.scenarios import ScenarioRepository
from app.schemas import (
    ConstraintResult,
    MapPayload,
    OptimizationRunRead,
    PackingItem,
    PackingPlan,
    ProviderAvailability,
    RouteStopRead,
    RunMetrics,
    ScenarioRead,
    StageEventRead,
    StopRead,
    VehicleRead,
)
from app.services.events import broker
from app.services.map_data import MapDataService


class OptimizationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.scenarios = ScenarioRepository(session)
        self.runs = OptimizationRepository(session)
        self.provider = HaversineProvider()
        self.optimizer = RouteOptimizer(self.provider, self.settings)
        self.metrics_engine = MetricsEngine(self.settings)
        self.predictions = NoPredictionProvider()
        self.intelligence = NoIntelligenceProvider()

    async def create_run(self, scenario_id: uuid.UUID, vehicle_id: uuid.UUID | None = None) -> OptimizationRun:
        scenario = await self.scenarios.get(scenario_id, include_children=True)
        if not scenario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
        if not scenario.stops:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Scenario has no stops")
        if not scenario.vehicles:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Scenario has no vehicles")
        run = await self.runs.create(scenario.id, self.settings.algorithm_version, self.provider.name, vehicle_id)
        await self._event(run, EventType.RUN_CREATED, {"stop_count": len(scenario.stops)})
        await self.session.commit()
        return run

    async def execute(self, run_id: uuid.UUID) -> None:
        run = await self.runs.get(run_id, full=True)
        if not run:
            return
        timings: dict[str, float] = {}
        total_start = perf_counter()
        try:
            await self._stage(run, EventType.VALIDATING, RunStatus.VALIDATING, {"scenario_id": str(run.scenario_id)})
            scenario = run.scenario
            stops = scenario.stops
            vehicles = scenario.vehicles
            await self._stage(run, EventType.LOADING_DATA, RunStatus.VALIDATING, {"stops": len(stops), "vehicles": len(vehicles)})
            depot = Location(scenario.depot_lat, scenario.depot_lng)

            started = perf_counter()
            baseline = await asyncio.to_thread(self.optimizer.baseline, stops, vehicles, depot)
            timings["baseline_ms"] = self._elapsed(started)

            await self._stage(run, EventType.CLUSTERING, RunStatus.OPTIMIZING, {"provider": self.provider.name})
            started = perf_counter()
            optimized = await asyncio.to_thread(self.optimizer.optimize, stops, vehicles, depot)
            timings["optimization_ms"] = self._elapsed(started)
            await self._event(run, EventType.BUILDING_ROUTE, {"vehicles": len(optimized.routes), "clusters": optimized.cluster_count}, timings["optimization_ms"])
            await self._event(run, EventType.OPTIMIZING, {"algorithm": self.settings.algorithm_version})

            run.status = RunStatus.VALIDATING_ROUTE
            started = perf_counter()
            constraints = optimized.constraints
            timings["constraints_ms"] = self._elapsed(started)
            await self._event(run, EventType.CHECKING_CONSTRAINTS, {"feasible": constraints.feasible, "violations": len(constraints.violations)}, timings["constraints_ms"])

            started = perf_counter()
            metrics = self.metrics_engine.calculate(baseline, optimized, vehicles)
            timings["metrics_ms"] = self._elapsed(started)
            await self._event(run, EventType.CALCULATING_METRICS, {"distance_saved_km": metrics["distance"]["saved_km"]}, timings["metrics_ms"])

            started = perf_counter()
            route_models = self._route_models(run, optimized.stops)
            await self.runs.replace_route(run, route_models)
            self._persist_results(run, optimized, metrics, timings)
            timings["persistence_ms"] = self._elapsed(started)
            run.stage_timings = timings
            await self._event(run, EventType.PERSISTING, {"route_stops": len(route_models)}, timings["persistence_ms"])
            run.status = RunStatus.COMPLETED
            run.system_state = "ROUTE_READY"
            run.completed_at = datetime.now(UTC)
            run.optimization_latency_ms = self._elapsed(total_start)
            await self._event(run, EventType.ROUTE_READY, {"distance_km": optimized.total_distance_km, "feasible": constraints.feasible}, run.optimization_latency_ms)
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            run = await self.runs.get(run_id)
            if run:
                run.status = RunStatus.FAILED
                run.error_message = str(exc)
                run.completed_at = datetime.now(UTC)
                await self.session.commit()
            logger.exception("optimization_failed", run_id=str(run_id), error=str(exc))

    async def get(self, run_id: uuid.UUID | str) -> OptimizationRunRead:
        run = await self.runs.get(run_id, full=True)
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization run not found")
        return await self.serialize(run)

    async def map_data(self, run_id: uuid.UUID | str) -> MapPayload:
        run = await self.runs.get(run_id, full=True)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Optimization run not found",
            )
        serialized = await self.serialize(run)
        baseline = await asyncio.to_thread(
            self.optimizer.baseline,
            run.scenario.stops,
            run.scenario.vehicles,
            Location(run.scenario.depot_lat, run.scenario.depot_lng),
        )
        reoptimization_latency = next(
            (
                event.duration_ms
                for event in sorted(
                    run.events,
                    key=lambda item: item.created_at,
                    reverse=True,
                )
                if event.event_type == EventType.ROUTE_UPDATED
                and event.duration_ms is not None
            ),
            None,
        )
        return MapDataService().build(
            scenario=serialized.scenario,
            stops=[StopRead.model_validate(stop) for stop in run.scenario.stops],
            baseline_routes=baseline.routes,
            optimized_route=serialized.route,
            events=serialized.events,
            predictions=serialized.intelligence.predictions,
            metrics=serialized.metrics,
            optimization_latency_ms=serialized.latency_ms,
            reoptimization_latency_ms=reoptimization_latency,
            run_id=serialized.run_id,
            system_state=serialized.system_state,
            intelligence=serialized.intelligence,
        )

    async def adapt(self, run: OptimizationRun, event_type: EventType, stop_id: uuid.UUID | None, payload: dict[str, Any]) -> OptimizationRunRead:
        if run.status != RunStatus.COMPLETED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only completed routes can accept trip events")
        run_uuid = run.id
        previous_distance = run.optimized_distance_km
        total_started = perf_counter()
        await self._event(run, event_type, payload, stop_id=stop_id)
        scenario_stop = next((stop for stop in run.scenario.stops if stop.id == stop_id), None)
        if scenario_stop and event_type in {
            EventType.STOP_CANCELLED,
            EventType.DELIVERY_FAILED,
            EventType.RETURN_CANCELLED,
        }:
            scenario_stop.status = (
                StopStatus.FAILED
                if event_type == EventType.DELIVERY_FAILED
                else StopStatus.CANCELLED
            )
        elif scenario_stop and event_type in {
            EventType.DELIVERY_COMPLETED,
            EventType.RETURN_COLLECTED,
        }:
            scenario_stop.status = StopStatus.COMPLETED

        excluded_external_ids = {
            stop.external_id
            for stop in run.scenario.stops
            if stop.status in {
                StopStatus.CANCELLED,
                StopStatus.FAILED,
                StopStatus.COMPLETED,
            }
        }
        current_routes = self._current_routes(run)
        run.system_state = "REOPTIMIZING"
        await self._event(
            run,
            EventType.REOPTIMIZING,
            {"trigger": event_type.value},
            stop_id=stop_id,
        )
        depot = Location(run.scenario.depot_lat, run.scenario.depot_lng)
        repair_started = perf_counter()
        repair = await asyncio.to_thread(
            IncrementalOptimizer(self.optimizer).repair,
            current_routes,
            run.scenario.stops,
            run.scenario.vehicles,
            depot,
            excluded_external_ids,
            cluster_count=run.cluster_count,
        )
        repair_compute_ms = self._elapsed(repair_started)
        await self.runs.replace_route(run, self._route_models(run, repair.plan.stops))
        baseline = await asyncio.to_thread(
            self.optimizer.baseline,
            run.scenario.stops,
            run.scenario.vehicles,
            depot,
        )
        metrics = self.metrics_engine.calculate(
            baseline,
            repair.plan,
            run.scenario.vehicles,
        )
        timings = {
            **(run.stage_timings or {}),
            "repair_compute_ms": repair_compute_ms,
        }
        self._persist_results(
            run,
            repair.plan,
            metrics,
            timings,
            preserve_baseline=True,
        )
        run.system_state = "TRIP_CHANGED"
        reoptimization_latency_ms = self._elapsed(total_started)
        timings["reoptimization_ms"] = reoptimization_latency_ms
        run.stage_timings = timings
        await self._event(
            run,
            EventType.ROUTE_UPDATED,
            {
                "distance_km": repair.plan.total_distance_km,
                "previous_distance_km": previous_distance,
                "remaining_stops": len(run.scenario.stops)
                - len(excluded_external_ids),
                "repair_compute_ms": repair_compute_ms,
                "affected_vehicle_sequence": repair.affected_vehicle_sequence,
                "removed_stop_ids": repair.removed_stop_ids,
                "previous_stop_ids": repair.previous_stop_ids,
                "updated_stop_ids": repair.updated_stop_ids,
                "changed_segment_stop_ids": repair.changed_segment_stop_ids,
            },
            reoptimization_latency_ms,
            stop_id=stop_id,
        )
        await self.session.commit()
        from app.services.intelligence import analyze_run

        await analyze_run(run_uuid, {"event_type": event_type.value, "payload": payload})
        self.session.expire_all()
        refreshed = await self.runs.get(run_uuid, full=True)
        assert refreshed is not None
        return await self.serialize(refreshed)

    async def serialize(self, run: OptimizationRun) -> OptimizationRunRead:
        scenario_repo = ScenarioRepository(self.session)
        total, deliveries, returns = await scenario_repo.counts(run.scenario.id)
        scenario = ScenarioRead.model_validate(run.scenario).model_copy(update={"stop_count": total, "delivery_count": deliveries, "return_count": returns})
        routes = [self._route_read(item, run.scenario) for item in sorted(run.route_stops, key=lambda value: value.sequence_number)]
        metrics = self._metrics_from_run(run)
        violations = run.constraint_violations or []
        packing = self._packing(run, routes)
        prediction = self.predictions.predict(run.scenario.stops, {"run_id": run.public_id})
        analysis = max(run.ai_analyses, key=lambda item: item.created_at) if run.ai_analyses else None
        intelligence = ProviderAvailability(
            status=ProviderStatus(analysis.status) if analysis else ProviderStatus.UNAVAILABLE,
            provider=analysis.provider if analysis else None,
            message=("Azure OpenAI analysis complete." if analysis and analysis.status == ProviderStatus.AVAILABLE.value else "Azure OpenAI intelligence is unavailable for this run."),
            model=analysis.model if analysis else None,
            model_version=analysis.model_version if analysis else None,
            latency_ms=analysis.latency_ms if analysis else None,
            summary=analysis.summary if analysis else None,
            predictions=analysis.predictions if analysis else [],
            recommendations=analysis.recommendations if analysis else [],
        )
        return OptimizationRunRead(
            id=run.id,
            run_id=run.public_id,
            scenario=scenario,
            vehicles=[VehicleRead.model_validate(item) for item in run.scenario.vehicles],
            status=run.status,
            system_state=run.system_state,
            algorithm_version=run.algorithm_version,
            routing_provider=run.routing_provider,
            started_at=run.started_at,
            completed_at=run.completed_at,
            stop_count=run.stop_count,
            cluster_count=run.cluster_count,
            latency_ms=run.optimization_latency_ms,
            stage_timings=run.stage_timings or {},
            route=routes,
            metrics=metrics,
            constraints=ConstraintResult(feasible=not violations, violations=violations),
            packing=packing,
            prediction=ProviderAvailability(status=prediction.status, provider=prediction.provider, message=prediction.message),
            intelligence=intelligence,
            events=[StageEventRead.model_validate(item) for item in sorted(run.events, key=lambda value: value.created_at)],
            error_message=run.error_message,
        )

    async def _stage(self, run: OptimizationRun, event_type: EventType, run_status: RunStatus, payload: dict[str, Any]) -> None:
        run.status = run_status
        await self._event(run, event_type, payload)
        await self.session.commit()

    async def _event(
        self,
        run: OptimizationRun,
        event_type: EventType,
        payload: dict[str, Any],
        duration_ms: float | None = None,
        *,
        stop_id: uuid.UUID | None = None,
    ) -> None:
        event = await self.runs.add_event(
            run,
            event_type,
            payload,
            duration_ms,
            stop_id=stop_id,
        )
        await self.session.flush()
        data = StageEventRead.model_validate(event).model_dump(mode="json")
        await broker.publish(run.id, data)
        logger.info("optimization_stage", run_id=run.public_id, scenario_id=str(run.scenario_id), stage=event_type.value, duration_ms=duration_ms, stop_count=run.stop_count, algorithm_version=run.algorithm_version)

    def _persist_results(
        self,
        run: OptimizationRun,
        plan: Any,
        metrics: dict[str, Any],
        timings: dict[str, float],
        *,
        preserve_baseline: bool = False,
    ) -> None:
        run.stop_count = sum(1 for item in plan.stops if item.stop is not None)
        run.cluster_count = plan.cluster_count
        if not preserve_baseline or run.baseline_distance_km is None:
            run.baseline_distance_km = metrics["distance"]["before_km"]
            run.baseline_fuel_l = metrics["fuel_litres"]["before"]
            run.baseline_fuel_cost = metrics["fuel_cost"]["before"]
            run.baseline_co2_kg = metrics["co2_kg"]["before"]
            run.baseline_driver_hours = metrics["driver_hours"]["before"]
        run.optimized_distance_km = metrics["distance"]["after_km"]
        run.optimized_fuel_l = metrics["fuel_litres"]["after"]
        run.optimized_fuel_cost = metrics["fuel_cost"]["after"]
        run.optimized_co2_kg = metrics["co2_kg"]["after"]
        run.optimized_driver_hours = metrics["driver_hours"]["after"]
        run.constraint_violations = [vars(item) for item in plan.constraints.violations]
        run.stage_timings = timings

    @staticmethod
    def _current_routes(run: OptimizationRun) -> list[list[RouteStop]]:
        grouped: dict[int, list[RouteStop]] = {}
        for item in sorted(run.route_stops, key=lambda value: value.sequence_number):
            grouped.setdefault(item.vehicle_sequence, []).append(item)
        return [grouped[key] for key in sorted(grouped)]

    def _route_models(self, run: OptimizationRun, route: list[Any]) -> list[RouteStop]:
        return [RouteStop(optimization_run_id=run.id, stop_id=item.stop.id if item.stop else None, vehicle_sequence=item.vehicle_sequence, sequence_number=item.sequence_number, action=item.action, arrival_time=item.arrival_time, departure_time=item.departure_time, load_before_kg=item.load_before_kg, load_after_kg=item.load_after_kg, load_before_l=item.load_before_l, load_after_l=item.load_after_l, distance_from_previous_km=item.distance_from_previous_km, status=StopStatus.PENDING) for item in route]

    @staticmethod
    def _route_read(item: RouteStop, scenario: Any) -> RouteStopRead:
        stop = item.stop
        return RouteStopRead(sequence_number=item.sequence_number, vehicle_sequence=item.vehicle_sequence, stop_id=item.stop_id, external_id=stop.external_id if stop else "DEPOT", name=(stop.address.split(",")[1].strip() if stop and "," in stop.address else "Depot"), address=stop.address if stop else scenario.depot_address, lat=stop.lat if stop else scenario.depot_lat, lng=stop.lng if stop else scenario.depot_lng, type=stop.type if stop else "WAREHOUSE", action=item.action, arrival_time=item.arrival_time, departure_time=item.departure_time, load_before_kg=item.load_before_kg, load_after_kg=item.load_after_kg, load_before_l=item.load_before_l, load_after_l=item.load_after_l, distance_from_previous_km=item.distance_from_previous_km, status=item.status)

    def _metrics_from_run(self, run: OptimizationRun) -> RunMetrics | None:
        required = [run.baseline_distance_km, run.optimized_distance_km, run.baseline_fuel_l, run.optimized_fuel_l, run.baseline_fuel_cost, run.optimized_fuel_cost, run.baseline_co2_kg, run.optimized_co2_kg, run.baseline_driver_hours, run.optimized_driver_hours]
        if any(value is None for value in required):
            return None
        before_labor = run.baseline_driver_hours * self.settings.driver_cost_per_hour  # type: ignore[operator]
        after_labor = run.optimized_driver_hours * self.settings.driver_cost_per_hour  # type: ignore[operator]
        def pair(before: float, after: float) -> dict[str, float]:
            return MetricsEngine._pair(before, after)
        return RunMetrics.model_validate({"distance": {"before_km": run.baseline_distance_km, "after_km": run.optimized_distance_km, "saved_km": max(0, run.baseline_distance_km - run.optimized_distance_km), "saved_percent": max(0, (run.baseline_distance_km - run.optimized_distance_km) / run.baseline_distance_km * 100) if run.baseline_distance_km else 0}, "fuel_litres": pair(run.baseline_fuel_l, run.optimized_fuel_l), "fuel_cost": pair(run.baseline_fuel_cost, run.optimized_fuel_cost), "co2_kg": pair(run.baseline_co2_kg, run.optimized_co2_kg), "driver_hours": pair(run.baseline_driver_hours, run.optimized_driver_hours), "labor_cost": pair(before_labor, after_labor), "total_cost": pair(run.baseline_fuel_cost + before_labor, run.optimized_fuel_cost + after_labor)})  # type: ignore[operator]

    @staticmethod
    def _packing(run: OptimizationRun, routes: list[RouteStopRead]) -> PackingPlan | None:
        if not run.scenario.vehicles:
            return None
        vehicle = run.scenario.vehicles[0]
        first_route = [item for item in routes if item.vehicle_sequence == 1 and item.stop_id]
        initial_kg = first_route[0].load_before_kg if first_route else 0
        initial_l = first_route[0].load_before_l if first_route else 0
        items = [PackingItem(sequence=index + 1, stop_id=item.external_id, action=item.action, weight_kg=abs(item.load_before_kg - item.load_after_kg), volume_l=abs(item.load_before_l - item.load_after_l), zone="DELIVERY" if item.action == RouteAction.DELIVER else "RETURN_ACCESS") for index, item in enumerate(first_route)]
        utilization = max(initial_kg / vehicle.capacity_kg if vehicle.capacity_kg else 0, initial_l / vehicle.capacity_l if vehicle.capacity_l else 0) * 100
        return PackingPlan(capacity_kg=vehicle.capacity_kg, capacity_l=vehicle.capacity_l, initial_load_kg=initial_kg, initial_load_l=initial_l, utilization_percent=round(utilization, 2), items=items)

    @staticmethod
    def _elapsed(started: float) -> float:
        return round((perf_counter() - started) * 1000, 3)
