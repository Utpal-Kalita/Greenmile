from types import SimpleNamespace

from app.ai.azure_openai import AzureOpenAIIntelligenceProvider
from app.ai.schemas import RouteIntelligence
from app.core.config import Settings
from app.domain.enums import ProviderStatus


async def test_reasoning_model_uses_bounded_low_effort(monkeypatch):
    request: dict[str, object] = {}

    class FakeCompletions:
        async def parse(self, **kwargs):
            request.update(kwargs)
            parsed = RouteIntelligence(
                summary="Route is ready.",
                return_insights=[],
                recommendations=[],
            )
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))]
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.beta = SimpleNamespace(
                chat=SimpleNamespace(completions=FakeCompletions())
            )

        async def close(self):
            return None

    monkeypatch.setattr("app.ai.azure_openai.AsyncAzureOpenAI", FakeClient)
    settings = Settings.model_validate(
        {
            "azure_openai_endpoint": "https://example.openai.azure.com",
            "azure_openai_api_key": "test-key",
            "azure_openai_deployment": "gpt-reasoning",
        }
    )

    result, _ = await AzureOpenAIIntelligenceProvider(settings).analyze({"run_id": "GM-TEST"})

    assert result.status == ProviderStatus.AVAILABLE
    assert request.get("reasoning_effort") == "low"
    assert request.get("max_completion_tokens") == 4096
