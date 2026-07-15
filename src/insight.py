"""OpenAI-compatible adapter, prompt guardrails and deterministic fallback."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any, Protocol

from src.models import AnalysisResult, InsightPayload, InsightResult

if TYPE_CHECKING:
    from src.config import AppConfig


LOGGER = logging.getLogger(__name__)
NUMBER_PATTERN = re.compile(r"(?<![\w])[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?")


class InsightProvider(Protocol):
    provider_name: str

    def generate(self, payload: InsightPayload) -> str:
        ...


class TemplateInsightProvider:
    provider_name = "template"

    def generate(self, payload: InsightPayload) -> str:
        overview = payload.overview
        top_product = payload.top_products[0] if payload.top_products else None
        top_region = payload.top_regions[0] if payload.top_regions else None
        trend = payload.trend
        anomaly_count = int(payload.anomalies.get("count", 0))

        parts = [
            f"本次分析 {int(overview.get('valid_orders', 0))} 笔有效订单，"
            f"已完成订单销售额为 {float(overview.get('total_sales', 0)):,.2f} 元，"
            f"平均订单金额 {float(overview.get('average_order_value', 0)):,.2f} 元。"
        ]
        if top_product:
            parts.append(
                f"销售额最高的商品是{top_product['product']}，贡献 {float(top_product['sales']):,.2f} 元。"
            )
        if top_region:
            parts.append(
                f"领先地区为{top_region['region']}，销售额 {float(top_region['sales']):,.2f} 元。"
            )
        if trend.get("highest_sales_date"):
            parts.append(
                f"峰值出现在 {trend['highest_sales_date']}，当日销售额 {float(trend['highest_sales']):,.2f} 元。"
            )
        parts.append(f"检测到 {anomaly_count} 条需关注记录，建议核验异常订单并持续跟踪退款结构。")
        return "".join(parts)[:300]


class OpenAICompatibleInsightProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        provider_name: str = "custom",
        timeout: float = 30.0,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("API Key 未配置")
        if not model.strip():
            raise ValueError("模型名称未配置")
        if not base_url.strip():
            raise ValueError("Base URL 未配置")
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.client = client
        self.model = model
        self.provider_name = provider_name.strip().lower() or "custom"

    def generate(self, payload: InsightPayload) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            max_tokens=450,
            messages=[
                {"role": "system", "content": self._system_prompt()},
                {
                    "role": "user",
                    "content": "请解释以下经过程序校验的聚合结果：\n"
                    + json.dumps(payload.model_dump(mode="json"), ensure_ascii=False),
                },
            ],
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise ValueError("模型返回空内容")
        return content.strip()[:300]

    @staticmethod
    def _system_prompt() -> str:
        return (
            "你是一名谨慎的数据分析师。只能依据用户提供的聚合 JSON 生成中文洞察；"
            "不得虚构数字，不得改变统计口径，不得自行重新计算指标。"
            "按整体表现、趋势、异常风险、业务建议组织为一段自然语言，不使用编号列表；"
            "金额统一使用元，不确定时明确说明，全文不超过300字。"
        )


class DeepSeekInsightProvider(OpenAICompatibleInsightProvider):
    """Backward-compatible DeepSeek preset for existing integrations."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "deepseek-v4-flash",
        base_url: str = "https://api.deepseek.com",
        timeout: float = 30.0,
        client: Any | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            provider_name="deepseek",
            timeout=timeout,
            client=client,
        )


class InsightProviderFactory:
    @staticmethod
    def create(config: "AppConfig") -> InsightProvider:
        if not config.enable_llm or not config.llm_api_key.strip():
            return TemplateInsightProvider()
        return OpenAICompatibleInsightProvider(
            api_key=config.llm_api_key,
            model=config.llm_model,
            base_url=config.llm_base_url,
            provider_name=config.llm_provider,
            timeout=config.llm_timeout_seconds,
        )


class InsightService:
    def __init__(self, provider: InsightProvider, fallback: InsightProvider | None = None) -> None:
        self.provider = provider
        self.fallback = fallback or TemplateInsightProvider()

    def generate(self, payload: InsightPayload) -> InsightResult:
        if isinstance(self.provider, TemplateInsightProvider):
            return InsightResult(
                text=self.provider.generate(payload),
                is_fallback=True,
                provider="template",
                warning="AI 模型未启用或未配置，已使用确定性模板摘要。",
            )

        last_error: Exception | None = None
        for _ in range(2):
            try:
                text = self.provider.generate(payload)
                if not self._numbers_are_grounded(text, payload):
                    raise ValueError("模型输出包含输入 JSON 之外的数字")
                return InsightResult(
                    text=text,
                    is_fallback=False,
                    provider=self.provider.provider_name,
                )
            except Exception as exc:  # External failures are intentionally degraded.
                last_error = exc
                LOGGER.warning("Insight generation failed: %s", type(exc).__name__)

        return InsightResult(
            text=self.fallback.generate(payload),
            is_fallback=True,
            provider="template",
            warning=f"AI 洞察不可用，已降级：{type(last_error).__name__}",
        )

    @staticmethod
    def _numbers_are_grounded(text: str, payload: InsightPayload) -> bool:
        allowed: list[float] = []

        def collect(value: Any) -> None:
            if isinstance(value, bool):
                return
            if isinstance(value, (int, float)):
                allowed.append(float(value))
            elif isinstance(value, str):
                for token in re.findall(r"\d+(?:\.\d+)?", value):
                    allowed.append(float(token))
            elif isinstance(value, dict):
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(payload.model_dump(mode="json"))
        for token in NUMBER_PATTERN.findall(text):
            is_percent = token.endswith("%")
            normalized = token.rstrip("%").replace(",", "")
            candidate = float(normalized) / 100 if is_percent else float(normalized)
            if not any(abs(candidate - value) <= max(0.005, abs(value) * 0.0001) for value in allowed):
                return False
        return True


def build_insight_payload(
    analysis: AnalysisResult,
    anomalies: list[dict[str, Any]],
) -> InsightPayload:
    highest = max(analysis.daily_sales, key=lambda row: row["sales"], default={})
    largest = max(
        (float(row.get("sales_amount", 0) or 0) for row in anomalies),
        default=0.0,
    )
    overview = analysis.overview.model_dump()
    return InsightPayload(
        overview=overview,
        top_products=analysis.top_products[:5],
        top_regions=analysis.top_regions[:5],
        trend={
            "highest_sales_date": highest.get("date"),
            "highest_sales": highest.get("sales", 0),
        },
        anomalies={"count": len(anomalies), "largest_order": largest},
    )
