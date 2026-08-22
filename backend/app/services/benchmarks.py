from __future__ import annotations

import uuid
from statistics import median, quantiles
from time import perf_counter

import psutil
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import BenchmarkRun
from app.optimizer.engine import HaversineProvider, Location, RouteOptimizer
from app.repositories.benchmarks import BenchmarkRepository
from app.repositories.scenarios import ScenarioRepository
from app.schemas import BenchmarkCreate


class BenchmarkService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = BenchmarkRepository(session)
        self.scenarios = ScenarioRepository(session)
        self.settings = get_settings()

    async def execute(self, payload: BenchmarkCreate) -> list[BenchmarkRun]:
        scenario = await (self.scenarios.get(payload.scenario_id, include_children=True) if payload.scenario_id else self.scenarios.get_demo())
        if not scenario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark scenario not found")
        optimizer = RouteOptimizer(HaversineProvider(), self.settings)
        depot = Location(scenario.depot_lat, scenario.depot_lng)
        created: list[BenchmarkRun] = []
        process = psutil.Process()
        for workload in payload.workloads:
            source = scenario.stops
            if not source:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Scenario has no stops")
            stops = [source[index % len(source)] for index in range(workload)]
            baseline_times: list[float] = []
            optimized_times: list[float] = []
            baseline = optimized = None
            stage_timings: dict[str, float | list[float]] = {}
            for _ in range(payload.repetitions):
                started = perf_counter()
                baseline = optimizer.baseline(stops, scenario.vehicles, depot)
                baseline_times.append((perf_counter() - started) * 1000)
                started = perf_counter()
                optimized = optimizer.optimize(stops, scenario.vehicles, depot)
                optimized_times.append((perf_counter() - started) * 1000)
            assert baseline is not None and optimized is not None
            ordered = sorted(optimized_times)
            quartiles = quantiles(ordered, n=100, method="inclusive") if len(ordered) > 1 else [ordered[0]] * 99
            stage_timings = {"baseline_median_ms": round(median(baseline_times), 3), "optimized_samples_ms": [round(value, 3) for value in ordered]}
            item = await self.repository.create(
                scenario_id=scenario.id,
                dataset_name=f"greenmile_{workload}",
                dataset_version=scenario.provenance.get("generator", "unknown"),
                stop_count=workload,
                baseline_algorithm="separate-delivery-return",
                optimized_algorithm=self.settings.algorithm_version,
                baseline_latency_ms=round(median(baseline_times), 3),
                optimized_latency_ms=round(median(optimized_times), 3),
                p50_latency_ms=round(median(optimized_times), 3),
                p95_latency_ms=round(quartiles[94], 3),
                p99_latency_ms=round(quartiles[98], 3),
                baseline_distance_km=baseline.total_distance_km,
                optimized_distance_km=optimized.total_distance_km,
                route_quality_delta=round((optimized.total_distance_km / baseline.total_distance_km - 1) * 100 if baseline.total_distance_km else 0, 3),
                constraint_violations=len(optimized.constraints.violations),
                memory_usage_mb=round(process.memory_info().rss / 1024 / 1024, 3),
                stage_timings=stage_timings,
            )
            created.append(item)
        await self.session.commit()
        return created

    async def list(self) -> list[BenchmarkRun]:
        return await self.repository.list()

    async def get(self, benchmark_id: uuid.UUID) -> BenchmarkRun:
        item = await self.repository.get(benchmark_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark not found")
        return item
