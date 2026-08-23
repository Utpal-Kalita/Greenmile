from __future__ import annotations

from time import perf_counter
from typing import Any

import openai
from openai import AsyncAzureOpenAI

from app.ai.schemas import RouteIntelligence
from app.core.config import Settings
from app.domain.enums import ProviderStatus
from app.providers.contracts import ProviderResult

SYSTEM_PROMPT = """You are Greenmile Intelligence, a concise logistics operations analyst.
The deterministic optimizer has already created the route. Never reorder stops, claim to calculate routes,
or invent history. Analyze only the supplied route and stop evidence. Produce a short actionable briefing,
up to twelve evidence-based return insights, and up to eight recommendations. Treat probabilities as
reasoned LLM estimates, not measured model predictions. Cite concrete stop IDs in each relevant reason."""


class AzureOpenAIIntelligenceProvider:
    name = "AZURE_OPENAI"

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.azure_openai_endpoint and self.settings.azure_openai_api_key and self.settings.azure_openai_deployment)

    async def analyze(self, route_context: dict[str, Any]) -> tuple[ProviderResult, float | None]:
        if not self.configured:
            return ProviderResult(ProviderStatus.UNAVAILABLE, None, "Azure OpenAI is not configured for this run."), None
        started = perf_counter()
        client = AsyncAzureOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.openai_api_version,
            timeout=self.settings.azure_openai_timeout_seconds,
            max_retries=self.settings.azure_openai_max_retries,
        )
        try:
            completion = await client.beta.chat.completions.parse(
                model=self.settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": str(route_context)},
                ],
                response_format=RouteIntelligence,
                reasoning_effort="low",
                max_completion_tokens=4096,
            )
            parsed = completion.choices[0].message.parsed
            if parsed is None:
                raise ValueError("Azure OpenAI returned no structured result")
            latency = round((perf_counter() - started) * 1000, 3)
            return ProviderResult(
                status=ProviderStatus.AVAILABLE,
                provider=self.name,
                message="Azure OpenAI analysis complete.",
                data=parsed.model_dump(mode="json"),
            ), latency
        except (openai.APIError, ValueError) as exc:
            latency = round((perf_counter() - started) * 1000, 3)
            return ProviderResult(
                status=ProviderStatus.UNAVAILABLE,
                provider=self.name,
                message="Azure OpenAI intelligence was unavailable for this run.",
                data={"error": type(exc).__name__},
            ), latency
        finally:
            await client.close()
