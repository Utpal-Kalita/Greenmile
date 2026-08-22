import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BenchmarkRun


class BenchmarkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **values: object) -> BenchmarkRun:
        benchmark = BenchmarkRun(**values)
        self.session.add(benchmark)
        await self.session.flush()
        return benchmark

    async def list(self) -> list[BenchmarkRun]:
        result = await self.session.scalars(select(BenchmarkRun).order_by(BenchmarkRun.created_at.desc()))
        return list(result)

    async def get(self, benchmark_id: uuid.UUID) -> BenchmarkRun | None:
        return await self.session.get(BenchmarkRun, benchmark_id)
