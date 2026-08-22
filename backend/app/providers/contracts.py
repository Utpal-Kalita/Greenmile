from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.enums import ProviderStatus


@dataclass(frozen=True)
class ProviderResult:
    status: ProviderStatus
    provider: str | None
    message: str
    data: dict[str, Any] | None = None


class ReturnPredictionProvider(Protocol):
    def predict(self, stops: Sequence[Any], context: dict[str, Any]) -> ProviderResult: ...


class IntelligenceProvider(Protocol):
    async def analyze(self, route_context: dict[str, Any]) -> ProviderResult: ...


class NoPredictionProvider:
    def predict(self, stops: Sequence[Any], context: dict[str, Any]) -> ProviderResult:
        return ProviderResult(
            status=ProviderStatus.UNAVAILABLE,
            provider=None,
            message="Return prediction is unavailable until a trained model is connected.",
        )


class NoIntelligenceProvider:
    async def analyze(self, route_context: dict[str, Any]) -> ProviderResult:
        return ProviderResult(
            status=ProviderStatus.UNAVAILABLE,
            provider=None,
            message="Greenmile Intelligence is unavailable until an AI provider is connected.",
        )
