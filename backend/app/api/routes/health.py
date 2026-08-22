from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import DatabaseSession
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok", service="greenmile-api", database="connected", version="3.0.0")


@router.get("/health/ready", response_model=HealthResponse)
async def readiness(session: DatabaseSession) -> HealthResponse:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return HealthResponse(status="degraded", service="greenmile-api", database="unavailable", version="3.0.0")
    return HealthResponse(status="ok", service="greenmile-api", database="connected", version="3.0.0")
