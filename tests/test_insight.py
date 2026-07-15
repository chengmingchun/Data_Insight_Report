from src.config import AppConfig
from src.insight import (
    DeepSeekInsightProvider,
    InsightProviderFactory,
    InsightService,
    OpenAICompatibleInsightProvider,
    TemplateInsightProvider,
)
from src.models import InsightPayload


PAYLOAD = InsightPayload(
    overview={
        "valid_orders": 6,
        "total_sales": 1780.0,
        "average_order_value": 445.0,
        "refund_rate": 1 / 6,
    },
    top_products=[{"product": "显示器", "sales": 900.0}],
    top_regions=[{"region": "华东", "sales": 1200.0}],
    trend={"highest_sales_date": "2026-06-02", "highest_sales": 900.0},
    anomalies={"count": 1, "largest_order": 10000.0},
)


class RaisingProvider:
    def generate(self, payload: InsightPayload) -> str:
        raise TimeoutError("timeout")


class HallucinatingProvider:
    def generate(self, payload: InsightPayload) -> str:
        return "销售额达到 999999 元。"


def test_template_fallback_contains_deterministic_metrics() -> None:
    text = TemplateInsightProvider().generate(PAYLOAD)
    assert "1,780.00" in text
    assert "显示器" in text


def test_service_falls_back_on_provider_error() -> None:
    result = InsightService(RaisingProvider()).generate(PAYLOAD)
    assert result.is_fallback is True
    assert "1,780.00" in result.text


def test_service_rejects_numbers_not_in_payload() -> None:
    result = InsightService(HallucinatingProvider()).generate(PAYLOAD)
    assert result.is_fallback is True
    assert "999999" not in result.text


def test_factory_uses_fallback_without_key() -> None:
    provider = InsightProviderFactory.create(AppConfig(llm_api_key=""))
    assert isinstance(provider, TemplateInsightProvider)


def test_factory_accepts_other_openai_compatible_providers() -> None:
    provider = InsightProviderFactory.create(
        AppConfig(
            llm_provider="openrouter",
            llm_api_key="not-a-real-key",
            llm_model="vendor/model-name",
            llm_base_url="https://openrouter.ai/api/v1",
        )
    )

    assert isinstance(provider, OpenAICompatibleInsightProvider)
    assert provider.provider_name == "openrouter"
    assert provider.model == "vendor/model-name"


def test_deepseek_adapter_sends_only_structured_payload() -> None:
    class Message:
        content = "销售额为 1780.0 元。"

    class Choice:
        message = Message()

    class Completions:
        def __init__(self) -> None:
            self.kwargs = None

        def create(self, **kwargs):
            self.kwargs = kwargs
            return type("Response", (), {"choices": [Choice()]})()

    completions = Completions()
    client = type("Client", (), {"chat": type("Chat", (), {"completions": completions})()})()
    provider = DeepSeekInsightProvider(api_key="not-a-real-key", client=client)
    text = provider.generate(PAYLOAD)
    assert text == "销售额为 1780.0 元。"
    assert "order_id" not in completions.kwargs["messages"][1]["content"]
