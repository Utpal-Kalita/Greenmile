"""Create Greenmile core schema.

Revision ID: 0001
Revises:
Create Date: 2026-08-22
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

scenario_status = postgresql.ENUM("DRAFT", "READY", "ARCHIVED", name="scenariostatus", create_type=False)
stop_type = postgresql.ENUM("DELIVERY", "RETURN", "PICKUP", name="stoptype", create_type=False)
stop_status = postgresql.ENUM("PENDING", "COMPLETED", "FAILED", "CANCELLED", name="stopstatus", create_type=False)
vehicle_status = postgresql.ENUM("AVAILABLE", "ACTIVE", "MAINTENANCE", name="vehiclestatus", create_type=False)
run_status = postgresql.ENUM("QUEUED", "VALIDATING", "OPTIMIZING", "VALIDATING_ROUTE", "COMPLETED", "FAILED", "CANCELLED", name="runstatus", create_type=False)
route_action = postgresql.ENUM("DEPOT_START", "DELIVER", "PICKUP", "RETURN", "DEPOT_END", name="routeaction", create_type=False)
event_type = postgresql.ENUM(
    "RUN_CREATED", "VALIDATING", "LOADING_DATA", "CLUSTERING", "BUILDING_ROUTE", "OPTIMIZING",
    "CHECKING_CONSTRAINTS", "CALCULATING_METRICS", "PERSISTING", "ROUTE_READY",
    "AI_ANALYSIS_STARTED", "AI_ANALYSIS_COMPLETE", "AI_ANALYSIS_FAILED",
    "DELIVERY_COMPLETED", "DELIVERY_FAILED", "RETURN_READY", "RETURN_COLLECTED", "RETURN_CANCELLED",
    "STOP_CANCELLED", "CAPACITY_CHANGED", "TRAFFIC_DELAY", "DRIVER_DELAY", "REOPTIMIZING", "ROUTE_UPDATED",
    name="eventtype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in (scenario_status, stop_type, stop_status, vehicle_status, run_status, route_action, event_type):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(180), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("city", sa.String(120), nullable=False), sa.Column("status", scenario_status, nullable=False),
        sa.Column("depot_lat", sa.Float(), nullable=False), sa.Column("depot_lng", sa.Float(), nullable=False),
        sa.Column("depot_address", sa.String(300), nullable=False), sa.Column("vehicle_count", sa.Integer(), nullable=False),
        sa.Column("vehicle_capacity_kg", sa.Float(), nullable=False), sa.Column("vehicle_capacity_l", sa.Float(), nullable=False),
        sa.Column("provenance", postgresql.JSONB(), nullable=False), sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scenarios_status", "scenarios", ["status"])
    op.create_index("ix_scenarios_is_demo", "scenarios", ["is_demo"])

    op.create_table(
        "stops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(80), nullable=False), sa.Column("type", stop_type, nullable=False),
        sa.Column("address", sa.String(300), nullable=False), sa.Column("lat", sa.Float(), nullable=False), sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False), sa.Column("volume_l", sa.Float(), nullable=False),
        sa.Column("time_window_start", sa.Time(), nullable=False), sa.Column("time_window_end", sa.Time(), nullable=False),
        sa.Column("service_time_seconds", sa.Integer(), nullable=False), sa.Column("return_count_30d", sa.Integer()),
        sa.Column("avg_delivery_confirm_minutes", sa.Float()), sa.Column("dispute_history_count", sa.Integer()),
        sa.Column("status", stop_status, nullable=False), sa.Column("data_provenance", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("scenario_id", "external_id", name="uq_stops_scenario_id"),
    )
    op.create_index("ix_stops_scenario_id", "stops", ["scenario_id"])
    op.create_index("ix_stops_status", "stops", ["status"])
    op.create_index("ix_stops_scenario_type", "stops", ["scenario_id", "type"])

    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_code", sa.String(60), nullable=False), sa.Column("capacity_kg", sa.Float(), nullable=False),
        sa.Column("capacity_l", sa.Float(), nullable=False), sa.Column("fuel_type", sa.String(30), nullable=False),
        sa.Column("fuel_efficiency_km_per_l", sa.Float(), nullable=False), sa.Column("driver_hourly_cost", sa.Float(), nullable=False),
        sa.Column("status", vehicle_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("scenario_id", "vehicle_code", name="uq_vehicles_scenario_id"),
    )
    op.create_index("ix_vehicles_scenario_id", "vehicles", ["scenario_id"])

    op.create_table(
        "optimization_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("public_id", sa.String(24), nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="SET NULL")),
        sa.Column("status", run_status, nullable=False), sa.Column("system_state", sa.String(40), nullable=False),
        sa.Column("algorithm_version", sa.String(80), nullable=False), sa.Column("routing_provider", sa.String(40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("stop_count", sa.Integer(), nullable=False), sa.Column("cluster_count", sa.Integer(), nullable=False),
        sa.Column("baseline_distance_km", sa.Float()), sa.Column("optimized_distance_km", sa.Float()),
        sa.Column("baseline_fuel_l", sa.Float()), sa.Column("optimized_fuel_l", sa.Float()),
        sa.Column("baseline_fuel_cost", sa.Float()), sa.Column("optimized_fuel_cost", sa.Float()),
        sa.Column("baseline_co2_kg", sa.Float()), sa.Column("optimized_co2_kg", sa.Float()),
        sa.Column("baseline_driver_hours", sa.Float()), sa.Column("optimized_driver_hours", sa.Float()),
        sa.Column("optimization_latency_ms", sa.Float()), sa.Column("stage_timings", postgresql.JSONB(), nullable=False),
        sa.Column("constraint_violations", postgresql.JSONB(), nullable=False), sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("public_id", name="uq_optimization_runs_public_id"),
    )
    op.create_index("ix_optimization_runs_public_id", "optimization_runs", ["public_id"])
    op.create_index("ix_optimization_runs_scenario_id", "optimization_runs", ["scenario_id"])
    op.create_index("ix_optimization_runs_status", "optimization_runs", ["status"])

    op.create_table(
        "route_stops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("optimization_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stops.id", ondelete="SET NULL")),
        sa.Column("vehicle_sequence", sa.Integer(), nullable=False), sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("action", route_action, nullable=False), sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=False), sa.Column("load_before_kg", sa.Float(), nullable=False),
        sa.Column("load_after_kg", sa.Float(), nullable=False), sa.Column("load_before_l", sa.Float(), nullable=False),
        sa.Column("load_after_l", sa.Float(), nullable=False), sa.Column("distance_from_previous_km", sa.Float(), nullable=False),
        sa.Column("status", stop_status, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("optimization_run_id", "sequence_number", name="uq_route_stops_optimization_run_id"),
    )
    op.create_index("ix_route_stops_optimization_run_id", "route_stops", ["optimization_run_id"])
    op.create_index("ix_route_stops_stop_id", "route_stops", ["stop_id"])
    op.create_index("ix_route_stops_run_vehicle", "route_stops", ["optimization_run_id", "vehicle_sequence"])

    op.create_table(
        "trip_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("optimization_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stop_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stops.id", ondelete="SET NULL")),
        sa.Column("event_type", event_type, nullable=False), sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("duration_ms", sa.Float()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trip_events_optimization_run_id", "trip_events", ["optimization_run_id"])
    op.create_index("ix_trip_events_run_created", "trip_events", ["optimization_run_id", "created_at"])

    op.create_table(
        "benchmark_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dataset_name", sa.String(160), nullable=False), sa.Column("dataset_version", sa.String(40), nullable=False),
        sa.Column("stop_count", sa.Integer(), nullable=False), sa.Column("baseline_algorithm", sa.String(80), nullable=False),
        sa.Column("optimized_algorithm", sa.String(80), nullable=False), sa.Column("baseline_latency_ms", sa.Float(), nullable=False),
        sa.Column("optimized_latency_ms", sa.Float(), nullable=False), sa.Column("p50_latency_ms", sa.Float(), nullable=False),
        sa.Column("p95_latency_ms", sa.Float(), nullable=False), sa.Column("p99_latency_ms", sa.Float(), nullable=False),
        sa.Column("baseline_distance_km", sa.Float(), nullable=False), sa.Column("optimized_distance_km", sa.Float(), nullable=False),
        sa.Column("route_quality_delta", sa.Float(), nullable=False), sa.Column("constraint_violations", sa.Integer(), nullable=False),
        sa.Column("memory_usage_mb", sa.Float(), nullable=False), sa.Column("stage_timings", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_benchmark_runs_scenario_id", "benchmark_runs", ["scenario_id"])


def downgrade() -> None:
    for table in ("benchmark_runs", "trip_events", "route_stops", "optimization_runs", "vehicles", "stops", "scenarios"):
        op.drop_table(table)
    bind = op.get_bind()
    for enum in (event_type, route_action, run_status, vehicle_status, stop_status, stop_type, scenario_status):
        enum.drop(bind, checkfirst=True)
