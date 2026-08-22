from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums import EventType, RouteAction, RunStatus, ScenarioStatus, StopStatus, StopType, VehicleStatus


class Scenario(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scenarios"

    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")
    city: Mapped[str] = mapped_column(String(120))
    status: Mapped[ScenarioStatus] = mapped_column(Enum(ScenarioStatus), default=ScenarioStatus.DRAFT, index=True)
    depot_lat: Mapped[float] = mapped_column(Float)
    depot_lng: Mapped[float] = mapped_column(Float)
    depot_address: Mapped[str] = mapped_column(String(300))
    vehicle_count: Mapped[int] = mapped_column(Integer, default=1)
    vehicle_capacity_kg: Mapped[float] = mapped_column(Float)
    vehicle_capacity_l: Mapped[float] = mapped_column(Float)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    stops: Mapped[list[Stop]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    vehicles: Mapped[list[Vehicle]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    optimization_runs: Mapped[list[OptimizationRun]] = relationship(back_populates="scenario", cascade="all, delete-orphan")


class Stop(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stops"
    __table_args__ = (UniqueConstraint("scenario_id", "external_id"), Index("ix_stops_scenario_type", "scenario_id", "type"))

    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(80))
    type: Mapped[StopType] = mapped_column(Enum(StopType))
    address: Mapped[str] = mapped_column(String(300))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    volume_l: Mapped[float] = mapped_column(Float)
    time_window_start: Mapped[time]
    time_window_end: Mapped[time]
    service_time_seconds: Mapped[int] = mapped_column(Integer, default=300)
    return_count_30d: Mapped[int | None]
    avg_delivery_confirm_minutes: Mapped[float | None] = mapped_column(Float)
    dispute_history_count: Mapped[int | None]
    status: Mapped[StopStatus] = mapped_column(Enum(StopStatus), default=StopStatus.PENDING, index=True)
    data_provenance: Mapped[str] = mapped_column(String(40), default="IMPORTED")

    scenario: Mapped[Scenario] = relationship(back_populates="stops")
    route_stops: Mapped[list[RouteStop]] = relationship(back_populates="stop")


class Vehicle(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("scenario_id", "vehicle_code"),)

    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    vehicle_code: Mapped[str] = mapped_column(String(60))
    capacity_kg: Mapped[float] = mapped_column(Float)
    capacity_l: Mapped[float] = mapped_column(Float)
    fuel_type: Mapped[str] = mapped_column(String(30), default="DIESEL")
    fuel_efficiency_km_per_l: Mapped[float] = mapped_column(Float)
    driver_hourly_cost: Mapped[float] = mapped_column(Float)
    status: Mapped[VehicleStatus] = mapped_column(Enum(VehicleStatus), default=VehicleStatus.AVAILABLE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scenario: Mapped[Scenario] = relationship(back_populates="vehicles")
    optimization_runs: Mapped[list[OptimizationRun]] = relationship(back_populates="vehicle")


class OptimizationRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "optimization_runs"

    public_id: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.QUEUED, index=True)
    system_state: Mapped[str] = mapped_column(String(40), default="OPTIMIZATION_RUNNING")
    algorithm_version: Mapped[str] = mapped_column(String(80))
    routing_provider: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stop_count: Mapped[int] = mapped_column(Integer, default=0)
    cluster_count: Mapped[int] = mapped_column(Integer, default=0)
    baseline_distance_km: Mapped[float | None] = mapped_column(Float)
    optimized_distance_km: Mapped[float | None] = mapped_column(Float)
    baseline_fuel_l: Mapped[float | None] = mapped_column(Float)
    optimized_fuel_l: Mapped[float | None] = mapped_column(Float)
    baseline_fuel_cost: Mapped[float | None] = mapped_column(Float)
    optimized_fuel_cost: Mapped[float | None] = mapped_column(Float)
    baseline_co2_kg: Mapped[float | None] = mapped_column(Float)
    optimized_co2_kg: Mapped[float | None] = mapped_column(Float)
    baseline_driver_hours: Mapped[float | None] = mapped_column(Float)
    optimized_driver_hours: Mapped[float | None] = mapped_column(Float)
    optimization_latency_ms: Mapped[float | None] = mapped_column(Float)
    stage_timings: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict)
    constraint_violations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scenario: Mapped[Scenario] = relationship(back_populates="optimization_runs")
    vehicle: Mapped[Vehicle | None] = relationship(back_populates="optimization_runs")
    route_stops: Mapped[list[RouteStop]] = relationship(back_populates="optimization_run", cascade="all, delete-orphan")
    events: Mapped[list[TripEvent]] = relationship(back_populates="optimization_run", cascade="all, delete-orphan")
    ai_analyses: Mapped[list[AIAnalysis]] = relationship(cascade="all, delete-orphan")


class RouteStop(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "route_stops"
    __table_args__ = (UniqueConstraint("optimization_run_id", "sequence_number"), Index("ix_route_stops_run_vehicle", "optimization_run_id", "vehicle_sequence"))

    optimization_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("optimization_runs.id", ondelete="CASCADE"), index=True)
    stop_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("stops.id", ondelete="SET NULL"), nullable=True, index=True)
    vehicle_sequence: Mapped[int] = mapped_column(Integer, default=1)
    sequence_number: Mapped[int]
    action: Mapped[RouteAction] = mapped_column(Enum(RouteAction))
    arrival_time: Mapped[datetime]
    departure_time: Mapped[datetime]
    load_before_kg: Mapped[float]
    load_after_kg: Mapped[float]
    load_before_l: Mapped[float]
    load_after_l: Mapped[float]
    distance_from_previous_km: Mapped[float]
    status: Mapped[StopStatus] = mapped_column(Enum(StopStatus), default=StopStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    optimization_run: Mapped[OptimizationRun] = relationship(back_populates="route_stops")
    stop: Mapped[Stop | None] = relationship(back_populates="route_stops")


class TripEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "trip_events"
    __table_args__ = (Index("ix_trip_events_run_created", "optimization_run_id", "created_at"),)

    optimization_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("optimization_runs.id", ondelete="CASCADE"), index=True)
    stop_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("stops.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    duration_ms: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    optimization_run: Mapped[OptimizationRun] = relationship(back_populates="events")


class AIAnalysis(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_analyses"

    optimization_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("optimization_runs.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(60))
    model: Mapped[str] = mapped_column(String(160))
    model_version: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    predictions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    recommendations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BenchmarkRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "benchmark_runs"

    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    dataset_name: Mapped[str] = mapped_column(String(160))
    dataset_version: Mapped[str] = mapped_column(String(40))
    stop_count: Mapped[int]
    baseline_algorithm: Mapped[str] = mapped_column(String(80))
    optimized_algorithm: Mapped[str] = mapped_column(String(80))
    baseline_latency_ms: Mapped[float]
    optimized_latency_ms: Mapped[float]
    p50_latency_ms: Mapped[float]
    p95_latency_ms: Mapped[float]
    p99_latency_ms: Mapped[float]
    baseline_distance_km: Mapped[float]
    optimized_distance_km: Mapped[float]
    route_quality_delta: Mapped[float]
    constraint_violations: Mapped[int]
    memory_usage_mb: Mapped[float]
    stage_timings: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
