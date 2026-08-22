# Greenmile Architecture

Greenmile separates facts, decisions, intelligence, and presentation.

```text
Next.js UI ── REST/SSE ── FastAPI ── Services ── Repositories ── PostgreSQL
                                  ├── Deterministic route engine
                                  └── Azure OpenAI (after ROUTE_READY)
```

## Source of truth

PostgreSQL owns scenarios, stops, vehicles, optimization runs, route stops, trip events, Azure OpenAI analyses, and benchmark runs. The frontend contains no logistics result fixtures and performs no distance, fuel, emissions, cost, feasibility, or optimization calculations.

## Request lifecycle

1. The UI requests the persisted demo scenario and stops.
2. `POST /api/optimization-runs` creates a durable run and returns immediately.
3. A FastAPI background task validates data, calculates a baseline, clusters stops, builds and improves routes, validates constraints, calculates metrics, and persists route stops.
4. Each real stage is recorded in `trip_events` and published over SSE.
5. `ROUTE_READY` ends the critical route path.
6. Azure OpenAI analysis runs afterward and is persisted separately in `ai_analyses`. Missing credentials or API failures do not invalidate the route.
7. Driver events are persisted and trigger deterministic reoptimization.

## Runtime services

`docker-compose.yml` runs:

- PostgreSQL 16 on `5432`
- FastAPI on `8000`
- Next.js on `3000`

Both application services have health checks. The backend entrypoint applies Alembic migrations and idempotently seeds the demo before starting Uvicorn.

## Data provenance

The built-in 500-stop Delhi NCR workload is deterministic synthetic planning data. Its generator, seed, and non-real-world status are persisted on the scenario and documented in `data/scenarios/delhi_500/manifest.json`. Imported CSV data is tagged as imported and validated before persistence.

## External providers

- Routing currently uses great-circle Haversine distance and returns `routing_provider: HAVERSINE`; it does not claim road distance.
- Azure OpenAI is configured only on the backend. It generates structured operational intelligence, never route order or feasibility.
- No custom ML model is included. The prediction contract reports unavailable until a trained provider is added.
