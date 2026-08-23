# Greenmile

Greenmile is a bidirectional last-mile planning system that combines outbound deliveries and inbound returns into depot-closed vehicle routes. It provides a persistent FastAPI backend, a deterministic optimization engine, an event-driven trip workflow, and a Next.js operations interface with interactive Leaflet maps.

The current application is version 3.0.0.

[Live demo](https://greenmile-seven.vercel.app/) | [Presentation](https://docs.google.com/presentation/d/16DIOttygRqafvQ5uakdc6B03lOPCy-Ll/edit?usp=sharing&ouid=111781734386739260632&rtpof=true&sd=true)

## What Is Implemented

- Persistent scenarios, stops, vehicles, optimization runs, route stops, metrics, events, benchmarks, and optional AI analyses in PostgreSQL.
- A deterministic 500-stop Delhi demo with explicit synthetic-data provenance.
- DBSCAN geographic clustering using Haversine distance.
- Multi-vehicle workload partitioning by weight and volume.
- Delivery-before-return route construction using nearest-neighbour ordering and optimized-v2 bounded 2-opt search.
- Cached distance lookups, constant-time edge deltas, safe candidate pruning, and explicit local-search budgets.
- Fail-closed capacity, time-window, precedence, depot-closure, route-completeness, and numeric validation.
- Separate delivery/return baseline routes for before-and-after comparisons.
- Incremental route repair after supported trip events.
- Server-Sent Events (SSE) for optimization and route-update progress.
- Route-level distance, fuel, emissions, labor, and total-cost metrics.
- Interactive Leaflet maps with OpenStreetMap-derived tiles, depot and stop markers, route lines, sequence numbers, popups, zooming, and panning.
- Optional post-route operational analysis through Azure OpenAI structured outputs.
- Reproducible 100, 500, 1,000, and 5,000-stop benchmark workloads with p50, p95, p99, CPU, memory, route-quality, correctness, and local-search instrumentation.

## Honest Boundaries

Greenmile is currently a decision-support demo, not a production dispatch platform.

- Route distances are straight-line Haversine estimates, not road-network paths.
- The optimizer does not use live traffic, GPS, weather, or driver telemetry.
- Azure OpenAI does not create or reorder routes. It analyzes the completed deterministic route.
- Return probabilities from Azure OpenAI are reasoned estimates, not predictions from a trained model.
- If Azure OpenAI is not configured, the route still completes and intelligence is reported as unavailable. No AI response is fabricated.
- The browser demo loads the persisted synthetic scenario. CSV import exists in the API but is not currently exposed as a frontend upload flow.
- Authentication, authorization, and multi-tenant isolation are not implemented.

## Architecture

```text
Next.js frontend
  |-- scenario and stop loading
  |-- optimization controls and SSE progress
  |-- Leaflet route visualization
  |-- impact, packing, benchmark, and driver views
  |
  v
FastAPI service
  |-- scenario and CSV import API
  |-- asynchronous optimization runs
  |-- trip events and incremental route repair
  |-- map and benchmark payloads
  |
  +--> deterministic optimizer
  |      DBSCAN -> partition -> nearest neighbour
  |      -> cached delta 2-opt -> fail-closed validation -> metrics
  |
  +--> optional Azure OpenAI analysis after routing
  |
  v
PostgreSQL
  scenarios, stops, vehicles, runs, routes, events, metrics,
  benchmarks, and AI analyses
```

### Route Lifecycle

1. Load the seeded demo or create a scenario through the API.
2. Store stops and vehicles in PostgreSQL.
3. Create an optimization run with `POST /api/optimization-runs`.
4. Validate inputs, cluster stops, build routes, check constraints, calculate metrics, and persist results.
5. Stream stage events to the browser over SSE.
6. Run optional Azure OpenAI analysis after deterministic routing completes.
7. Submit trip events to repair affected routes without reclustering or running a global 2-opt pass.

## Repository Layout

```text
Greenmile/
|-- backend/
|   |-- app/
|   |   |-- api/routes/          # Health, scenario, run, event, and benchmark endpoints
|   |   |-- ai/                  # Optional Azure OpenAI provider and schemas
|   |   |-- core/                # Settings and structured logging
|   |   |-- data_pipeline/       # CSV validation and deterministic demo seeding
|   |   |-- db/                  # SQLAlchemy models and async sessions
|   |   |-- optimizer/           # Core engine, optimized-v2 search, and validators
|   |   |-- benchmarks/          # Reproducible benchmark harness and CLI
|   |   |-- repositories/        # Persistence access
|   |   |-- services/            # Application orchestration and map payloads
|   |   |-- main.py              # FastAPI application entry point
|   |   `-- schemas.py           # API request and response models
|   |-- alembic/                 # PostgreSQL migrations
|   |-- tests/                   # API, optimizer, map, benchmark, and event tests
|   |-- Dockerfile
|   |-- entrypoint.sh            # Migrate, seed, then start Uvicorn
|   `-- requirements.txt
|-- frontend/
|   |-- src/app/                 # Next.js App Router pages
|   |-- src/components/          # Trip, map, results, system, and performance UI
|   |-- src/lib/api.ts           # Typed REST and SSE client
|   |-- src/types/api.ts         # Frontend API contracts
|   |-- Dockerfile
|   |-- next.config.ts
|   |-- package.json
|   `-- vercel.json
|-- data/demo_stops.csv          # Separate 42-row CSV import example
|-- benchmark-results/           # Checked-in Round 2 JSON and Markdown evidence
|-- BENCHMARK.md                 # Benchmark methodology and interpretation
|-- docker-compose.yml           # PostgreSQL, backend, and frontend
|-- environment.example          # Local environment template
`-- render.yaml                  # Render web-service definition
```

## Technology

| Layer | Current implementation |
| --- | --- |
| Frontend | Next.js 16.3, React 19, TypeScript, Tailwind CSS 4 |
| Maps | Leaflet with OpenStreetMap-derived CARTO tiles |
| API | FastAPI, Pydantic v2, Uvicorn |
| Persistence | PostgreSQL, SQLAlchemy 2 async, asyncpg, Alembic |
| Optimization | NumPy, scikit-learn DBSCAN, Haversine routing, cached delta 2-opt, fail-closed validation |
| Intelligence | Optional Azure OpenAI structured outputs through the OpenAI SDK |
| Infrastructure | Docker Compose, Vercel frontend configuration, Render backend configuration |

## Quick Start With Docker

### Prerequisites

- Docker Desktop or another Docker Compose-compatible runtime.
- Ports `3000`, `8000`, and `5432` available locally.

### Start the stack

```bash
cp environment.example .env
docker compose up --build
```

The backend container runs Alembic migrations and seeds the deterministic demo before starting Uvicorn.

Open:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Readiness: http://localhost:8000/health/ready

Azure OpenAI variables may remain empty. Optimization does not depend on AI availability.

## Manual Development

### Backend

The backend targets Python 3.13 and requires PostgreSQL.

```bash
docker compose up -d postgres

cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql+asyncpg://greenmile:greenmile@localhost:5432/greenmile
alembic upgrade head
python -m app.data_pipeline.seed
python -m uvicorn app.main:app --port 8000
```

To enable optional operational intelligence, also configure:

```bash
export AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com
export AZURE_OPENAI_API_KEY=replace-with-your-server-side-key
export AZURE_OPENAI_DEPLOYMENT=replace-with-your-deployment-name
export OPENAI_API_VERSION=2024-10-21
```

These values are server-only. Never expose the API key through a `NEXT_PUBLIC_` variable.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000`. Override it when necessary:

```bash
NEXT_PUBLIC_API_URL=https://your-api.example.com npm run dev
```

## Demo Workflow

1. Open http://localhost:3000.
2. Select **Try Delhi demo**.
3. Review the persisted 500-stop scenario and five-vehicle fleet.
4. Select **Optimize this trip**.
5. Watch validation, clustering, routing, constraint, metrics, persistence, and AI-analysis events.
6. Inspect the interactive map, before/after metrics, route timeline, constraints, packing plan, and driver action.
7. Submit a supported trip event to exercise incremental route repair.
8. Use the **Performance**, **System**, and **How it works** pages for benchmark and architecture views.

## API Reference

All domain endpoints use the `/api` prefix.

### Health

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service metadata and links |
| `GET` | `/health/live` | Process liveness |
| `GET` | `/health/ready` | Database readiness |
| `GET` | `/docs` | Swagger UI |

### Scenarios

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/scenarios` | List scenarios |
| `POST` | `/api/scenarios` | Create a scenario and its vehicles |
| `GET` | `/api/scenarios/demo` | Load the current seeded demo |
| `GET` | `/api/scenarios/{scenario_id}` | Read one scenario |
| `GET` | `/api/scenarios/{scenario_id}/stops` | List scenario stops |
| `GET` | `/api/scenarios/{scenario_id}/map` | Read baseline map GeoJSON |
| `POST` | `/api/scenarios/{scenario_id}/stops/import` | Replace stops from a CSV upload |

### Optimization Runs And Events

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/optimization-runs` | Queue a run for a scenario |
| `GET` | `/api/optimization-runs/{run_id}` | Read run status and results |
| `GET` | `/api/optimization-runs/{run_id}/route` | Read persisted route stops |
| `GET` | `/api/optimization-runs/{run_id}/map` | Read optimized map GeoJSON |
| `GET` | `/api/optimization-runs/{run_id}/events` | Read persisted stage and trip events |
| `GET` | `/api/optimization-runs/{run_id}/events/stream` | Stream events over SSE |
| `POST` | `/api/optimization-runs/{run_id}/events` | Submit a supported trip event |

Create a run with:

```json
{
  "scenario_id": "scenario-uuid",
  "vehicle_id": null
}
```

Supported trip events include delivery completion/failure, return readiness/collection/cancellation, stop cancellation, capacity changes, traffic delays, and driver delays.

### Benchmarks

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/benchmarks` | List persisted benchmark results |
| `POST` | `/api/benchmarks` | Execute configured workloads |
| `GET` | `/api/benchmarks/{benchmark_id}` | Read one benchmark result |

## CSV Import

CSV import replaces the stops for an existing scenario. Files must be UTF-8 encoded.

Required columns:

```text
stop_id,type,lat,lng,address,weight_kg,volume_l,time_window_start,time_window_end
```

Optional columns:

```text
service_time_seconds,return_count_30d,avg_delivery_confirm_minutes,
dispute_history_count,data_provenance
```

Validation includes coordinates, non-negative weight and volume, valid stop type, and `time_window_start < time_window_end`. Supported stop types are `DELIVERY`, `RETURN`, and `PICKUP`.

`data/demo_stops.csv` is a separate 42-row import example. It is not the same dataset as the database-backed 500-stop browser demo.

## Optimization Behavior

The active route pipeline combines `backend/app/optimizer/engine.py`, `backend/app/optimizer/optimized_v2.py`, and `backend/app/optimizer/validator.py`.

### Baseline

- Separates delivery and return workloads.
- Partitions each workload across the configured fleet.
- Produces independent depot-closed routes for comparison.

### Optimized Plan

- Clusters stops with DBSCAN using `eps = 3 km` and `min_samples = 2` by default.
- Balances stops across available vehicles by accumulated weight and volume.
- Orders deliveries first and returns/pickups second for every vehicle.
- Applies nearest-neighbour ordering and optimized-v2 bounded 2-opt improvement within each segment.
- Uses a per-segment distance cache and constant-time edge-delta evaluation.
- Safely prunes candidates that cannot improve the route and records search budgets, cache hits, candidate counts, improvements, timings, and stop reasons.
- Materializes arrival/departure times and load transitions.
- Fails closed when stops are missing or duplicated, values are non-finite, route distances disagree, depot closure fails, or operational constraints are violated.
- Persists route stops, metrics, violations, stage timings, and system state.

### Incremental Repair

Supported trip events can trigger route adaptation. Repair preserves unaffected vehicle order, removes cancelled/completed stops where applicable, rematerializes affected routes, rechecks constraints, and publishes updated events.

## Optional Azure OpenAI Analysis

Azure OpenAI runs after the deterministic route is persisted. It receives structured route and stop evidence and can return:

- A concise operational summary.
- Up to twelve return insights.
- Up to eight recommendations.

The system prompt explicitly prevents the model from claiming it calculated the route or from inventing operational history. Provider status, latency, model metadata, predictions, recommendations, and errors are persisted.

## Validation

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

### Backend

```bash
cd backend
ruff check app tests
mypy app
pytest
```

Round 2 benchmark methodology and reproduction commands are documented in `BENCHMARK.md`. Generated comparison artifacts are stored in `benchmark-results/` and summarized by the frontend Performance Lab.

## Deployment

### Frontend: Vercel

1. Import the repository in Vercel.
2. Set the project root directory to `frontend`.
3. Set `NEXT_PUBLIC_API_URL` to the public FastAPI origin.
4. Deploy as a Next.js project. `frontend/vercel.json` declares the framework.

The frontend needs no AI credentials.

### Backend: Render

`render.yaml` currently defines only the Python web process. It does not provision PostgreSQL, set `DATABASE_URL`, or run Alembic migrations and demo seeding. Before treating it as a complete deployment:

1. Provision PostgreSQL and set `DATABASE_URL`.
2. Set `CORS_ORIGINS` to the deployed frontend origin.
3. Run `alembic upgrade head` during release/startup.
4. Run `python -m app.data_pipeline.seed` when the demo is required.
5. Configure the optional `AZURE_OPENAI_*` variables, not `GEMINI_API_KEY`.

The Docker backend entrypoint already performs migration and seeding; the current Render start command does not.

## Data And Claims

The bundled demo is deterministic synthetic data generated with seed `20260822`. It is explicitly labeled `SYNTHETIC_DETERMINISTIC` and must not be presented as observed fleet performance.

Distance, fuel, emissions, labor, and cost savings shown by the application are calculated from the active scenario and configured assumptions. They should not be presented as universal savings or production benchmarks without external validation.

## License

No license file is currently included in this repository.
