import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AIAnalysis


class AIAnalysisRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **values: object) -> AIAnalysis:
        analysis = AIAnalysis(**values)
        self.session.add(analysis)
        await self.session.flush()
        return analysis

    async def latest(self, run_id: uuid.UUID) -> AIAnalysis | None:
        return await self.session.scalar(
            select(AIAnalysis)
            .where(AIAnalysis.optimization_run_id == run_id)
            .order_by(AIAnalysis.created_at.desc())
            .limit(1)
        )
