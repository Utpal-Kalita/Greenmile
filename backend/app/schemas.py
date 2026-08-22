from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import EventType, ProviderStatus, RouteAction, RunStatus, ScenarioStatus, StopStatus, StopType, VehicleStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = ""
    city: str = Field(min_length=2, max_length=120)
    depot_lat: float = Field(ge=-90, le=90)
    depot_lng: float = Field(ge=-180, le=180)
    depot_address: str = Field(min_length=2, max_length=300)
    vehicle_count: int = Field(default=1, ge=1, le=100)
    vehicle_capacity_kg: float = Field(gt=0)
    vehicle_capacity_l: float = Field(gt=0)
    provenance: dict[str, Any] = Field(default_factory=lambda: {"kind": "USER_CREATED"})


class ScenarioRead(ORMModel):
    id: uuid.UUID
    name: str
    description: str
    city: str
    status: ScenarioStatus
    depot_lat: float
    depot_lng: float
    depot_address: str
    vehicle_count: int
    vehicle_capacity_kg: float
    vehicle_capacity_l: float
    provenance: dict[str, Any]
    is_demo: bool
    created_at: datetime
    updated_at: datetime
    stop_count: int = 0
    delivery_count: int = 0
    return_count: int = 0


class StopImportRow(BaseModel):
    stop_id: str = Field(min_length=1, max_length=80)
    type: StopType
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: str = Field(min_length=2, max_length=300)
    weight_kg: float = Field(ge=0)
    volume_l: float = Field(ge=0)
    time_window_start: time
    time_window_end: time
    service_time_seconds: int = Field(default=300, ge=0, le=86400)
    return_count_30d: int | None = Field(default=None, ge=0)
    avg_delivery_confirm_minutes: float | None = Field(default=None, ge=0)
    dispute_history_count: int | None = Field(default=None, ge=0)
    data_provenance: str = "IMPORTED"

    @model_validator(mode="after")
    def validate_window(self) -> StopImportRow:
        if self.time_window_start >= self.time_window_end:
            raise ValueError("time_window_start must be before time_window_end")
        return self


class StopRead(ORMModel):
    id: uuid.UUID
    scenario_id: uuid.UUID
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
    return_count_30d: int | None
    avg_delivery_confirm_minutes: float | None
    dispute_history_count: int | None
    status: StopStatus
    data_provenance: str


class VehicleRead(ORMModel):
    id: uuid.UUID
    vehicle_code: str
    capacity_kg: float
    capacity_l: float
    fuel_type: str
    fuel_efficiency_km_per_l: float
    driver_hourly_cost: float
    status: VehicleStatus


class ImportErrorDetail(BaseModel):
    row: int
    field: str
    error: str


class ImportResult(BaseModel):
    scenario_id: uuid.UUID
    imported: int
    rejected: int
    errors: list[ImportErrorDetail] = Field(default_factory=list)


class OptimizationCreate(BaseModel):
    scenario_id: uuid.UUID
    vehicle_id: uuid.UUID | None = None


class RouteStopRead(BaseModel):
    sequence_number: int
    vehicle_sequence: int
    stop_id: uuid.UUID | None
    external_id: str
    name: str
    address: str
    lat: float
    lng: float
    type: StopType | Literal["WAREHOUSE"]
    action: RouteAction
    arrival_time: datetime
    departure_time: datetime
    load_before_kg: float
    load_after_kg: float
    load_before_l: float
    load_after_l: float
    distance_from_previous_km: float
    status: StopStatus


class DistanceMetrics(BaseModel):
    before_km: float
    after_km: float
    saved_km: float
    saved_percent: float


class MetricPair(BaseModel):
    before: float
    after: float
    saved: float
    saved_percent: float


class RunMetrics(BaseModel):
    distance: DistanceMetrics
    fuel_litres: MetricPair
    fuel_cost: MetricPair
    co2_kg: MetricPair
    driver_hours: MetricPair
    labor_cost: MetricPair
    total_cost: MetricPair


class ConstraintViolation(BaseModel):
    type: str
    message: str
    stop_id: str | None = None
    amount_kg: float | None = None
    amount_l: float | None = None


class ConstraintResult(BaseModel):
    feasible: bool
    violations: list[ConstraintViolation]


class StageEventRead(ORMModel):
    id: uuid.UUID
    event_type: EventType
    stop_id: uuid.UUID | None
    payload: dict[str, Any]
    duration_ms: float | None
    created_at: datetime


class ProviderAvailability(BaseModel):
    status: ProviderStatus
    provider: str | None = None
    message: str
    model: str | None = None
    model_version: str | None = None
    latency_ms: float | None = None
    summary: str | None = None
    predictions: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)


class PackingItem(BaseModel):
    sequence: int
    stop_id: str
    action: RouteAction
    weight_kg: float
    volume_l: float
    zone: Literal["DELIVERY", "RETURN_ACCESS"]


class PackingPlan(BaseModel):
    capacity_kg: float
    capacity_l: float
    initial_load_kg: float
    initial_load_l: float
    utilization_percent: float
    items: list[PackingItem]


class GeoJSONFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any] = Field(default_factory=dict)


class GeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoJSONFeature] = Field(default_factory=list)


class MapCenter(BaseModel):
    lat: float
    lng: float


class MapBounds(BaseModel):
    south: float
    west: float
    north: float
    east: float


class MapViewport(BaseModel):
    center: MapCenter
    bounds: MapBounds


class MapRoutes(BaseModel):
    baseline_delivery: GeoJSONFeatureCollection
    baseline_return: GeoJSONFeatureCollection
    optimized: GeoJSONFeatureCollection


class MapPerformance(BaseModel):
    optimization_latency_ms: float | None = None
    reoptimization_latency_ms: float | None = None


class MapPayload(BaseModel):
    scenario_id: uuid.UUID
    run_id: str | None = None
    system_state: str = "SCENARIO_READY"
    map: MapViewport
    stops: GeoJSONFeatureCollection
    warehouse: GeoJSONFeature
    routes: MapRoutes
    events: GeoJSONFeatureCollection = Field(default_factory=GeoJSONFeatureCollection)
    metrics: RunMetrics | None = None
    performance: MapPerformance = Field(default_factory=MapPerformance)
    intelligence: ProviderAvailability | None = None


class OptimizationRunRead(BaseModel):
    id: uuid.UUID
    run_id: str
    scenario: ScenarioRead
    vehicles: list[VehicleRead]
    status: RunStatus
    system_state: str
    algorithm_version: str
    routing_provider: str
    started_at: datetime | None
    completed_at: datetime | None
    stop_count: int
    cluster_count: int
    latency_ms: float | None
    stage_timings: dict[str, float]
    route: list[RouteStopRead]
    metrics: RunMetrics | None
    constraints: ConstraintResult
    packing: PackingPlan | None
    prediction: ProviderAvailability
    intelligence: ProviderAvailability
    events: list[StageEventRead]
    error_message: str | None


class TripEventCreate(BaseModel):
    event_type: EventType
    stop_id: uuid.UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class BenchmarkCreate(BaseModel):
    scenario_id: uuid.UUID | None = None
    workloads: list[int] = Field(default_factory=lambda: [100, 500, 1000, 2500, 5000])
    repetitions: int = Field(default=3, ge=1, le=10)

    @model_validator(mode="after")
    def validate_workloads(self) -> BenchmarkCreate:
        allowed = {100, 500, 1000, 2500, 5000}
        if not self.workloads or any(value not in allowed for value in self.workloads):
            raise ValueError("workloads must contain only 100, 500, 1000, 2500, or 5000")
        return self


class BenchmarkRead(ORMModel):
    id: uuid.UUID
    scenario_id: uuid.UUID
    dataset_name: str
    dataset_version: str
    stop_count: int
    baseline_algorithm: str
    optimized_algorithm: str
    baseline_latency_ms: float
    optimized_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    baseline_distance_km: float
    optimized_distance_km: float
    route_quality_delta: float
    constraint_violations: int
    memory_usage_mb: float
    stage_timings: dict[str, float]
    created_at: datetime


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    database: Literal["connected", "unavailable"]
    version: str
