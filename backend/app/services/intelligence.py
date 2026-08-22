from __future__ import annotations

import uuid

from app.ai.azure_openai import AzureOpenAIIntelligenceProvider
from app.core.config import get_settings
from app.db.session import SessionFactory
from app.domain.enums import EventType, ProviderStatus
from app.repositories.ai import AIAnalysisRepository
from app.repositories.runs import OptimizationRepository
from app.schemas import StageEventRead
from app.services.events import broker


async def analyze_run(run_id: uuid.UUID, change_context: dict | None = None) -> None:
    async with SessionFactory() as session:
        runs = OptimizationRepository(session)
        run = await runs.get(run_id, full=True)
        if not run:
            return
        provider = AzureOpenAIIntelligenceProvider(get_settings())
        started_event = await runs.add_event(run, EventType.AI_ANALYSIS_STARTED, {"provider": provider.name})
        await session.commit()
        await broker.publish(run.id, StageEventRead.model_validate(started_event).model_dump(mode="json"))

        route_context = {
            "run_id": run.public_id,
            "routing_provider": run.routing_provider,
            "distance_km": run.optimized_distance_km,
            "constraints": run.constraint_violations,
            "change_context": change_context,
            "stops": [
                {
                    "id": stop.external_id,
                    "type": stop.type.value,
                    "location": stop.address,
                    "weight_kg": stop.weight_kg,
                    "volume_l": stop.volume_l,
                    "return_count_30d": stop.return_count_30d,
                    "avg_delivery_confirm_minutes": stop.avg_delivery_confirm_minutes,
                    "dispute_history_count": stop.dispute_history_count,
                }
                for stop in run.scenario.stops[:100]
            ],
        }
        result, latency = await provider.analyze(route_context)
        data = result.data or {}
        await AIAnalysisRepository(session).create(
            optimization_run_id=run.id,
            provider=result.provider or provider.name,
            model=get_settings().azure_openai_deployment or "not-configured",
            model_version=get_settings().openai_api_version,
            status=result.status.value,
            summary=data.get("summary"),
            predictions=data.get("return_insights", []),
            recommendations=data.get("recommendations", []),
            latency_ms=latency,
            error_message=data.get("error") if result.status == ProviderStatus.UNAVAILABLE else None,
        )
        event_type = EventType.AI_ANALYSIS_COMPLETE if result.status == ProviderStatus.AVAILABLE else EventType.AI_ANALYSIS_FAILED
        event = await runs.add_event(run, event_type, {"status": result.status.value, "provider": result.provider, "message": result.message}, latency)
        await session.commit()
        await broker.publish(run.id, StageEventRead.model_validate(event).model_dump(mode="json"))
