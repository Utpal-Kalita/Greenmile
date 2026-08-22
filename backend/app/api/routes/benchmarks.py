import uuid

from fastapi import APIRouter, status

from app.api.dependencies import DatabaseSession
from app.schemas import BenchmarkCreate, BenchmarkRead
from app.services.benchmarks import BenchmarkService

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.post("", response_model=list[BenchmarkRead], status_code=status.HTTP_201_CREATED)
async def run_benchmarks(payload: BenchmarkCreate, session: DatabaseSession) -> list[BenchmarkRead]:
    return [BenchmarkRead.model_validate(item) for item in await BenchmarkService(session).execute(payload)]


@router.get("", response_model=list[BenchmarkRead])
async def list_benchmarks(session: DatabaseSession) -> list[BenchmarkRead]:
    return [BenchmarkRead.model_validate(item) for item in await BenchmarkService(session).list()]


@router.get("/{benchmark_id}", response_model=BenchmarkRead)
async def get_benchmark(benchmark_id: uuid.UUID, session: DatabaseSession) -> BenchmarkRead:
    return BenchmarkRead.model_validate(await BenchmarkService(session).get(benchmark_id))
