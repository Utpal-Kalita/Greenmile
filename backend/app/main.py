from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import benchmarks, health, optimization, scenarios
from app.core.config import get_settings
from app.core.logging import configure_logging, logger
from app.data_pipeline.seed import seed_demo
from app.db.session import close_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    if settings.auto_seed_demo:
        try:
            demo_id = await seed_demo()
            logger.info("demo_scenario_ready", scenario_id=demo_id)
        except Exception:
            logger.exception("demo_scenario_seed_failed")
            raise
    yield
    await close_database()


app = FastAPI(
    title=settings.app_name,
    description="Persistent bidirectional last-mile optimization API.",
    version="3.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Last-Event-ID"],
)
app.include_router(health.router)
app.include_router(scenarios.router, prefix=settings.api_prefix)
app.include_router(optimization.router, prefix=settings.api_prefix)
app.include_router(benchmarks.router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": "greenmile-api", "version": "3.0.0", "docs": "/docs", "health": "/health/ready"}
