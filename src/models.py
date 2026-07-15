"""Typed data transfer objects shared by application modules."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DataQualityReport(BaseModel):
    raw_rows: int = 0
    valid_rows: int = 0
    partial_rows: int = 0
    rejected_rows: int = 0
    duplicate_rows: int = 0
    missing_counts: dict[str, int] = Field(default_factory=dict)
    invalid_counts: dict[str, int] = Field(default_factory=dict)
    applied_rules: list[str] = Field(default_factory=list)


class OverviewMetrics(BaseModel):
    valid_orders: int = 0
    total_sales: float = 0.0
    average_order_value: float = 0.0
    total_quantity: int = 0
    refunded_orders: int = 0
    refund_rate: float = 0.0
    anomaly_count: int = 0


class AnalysisResult(BaseModel):
    overview: OverviewMetrics = Field(default_factory=OverviewMetrics)
    sales_by_region: list[dict[str, Any]] = Field(default_factory=list)
    sales_by_category: list[dict[str, Any]] = Field(default_factory=list)
    sales_by_product: list[dict[str, Any]] = Field(default_factory=list)
    orders_by_status: list[dict[str, Any]] = Field(default_factory=list)
    daily_sales: list[dict[str, Any]] = Field(default_factory=list)
    top_products: list[dict[str, Any]] = Field(default_factory=list)
    top_products_by_quantity: list[dict[str, Any]] = Field(default_factory=list)
    top_regions: list[dict[str, Any]] = Field(default_factory=list)
    top_categories: list[dict[str, Any]] = Field(default_factory=list)
    region_category_matrix: list[dict[str, Any]] = Field(default_factory=list)


class AnomalyResult(BaseModel):
    records: list[dict[str, Any]] = Field(default_factory=list)
    lower_bound: float | None = None
    upper_bound: float | None = None


class InsightPayload(BaseModel):
    overview: dict[str, Any]
    top_products: list[dict[str, Any]] = Field(default_factory=list)
    top_regions: list[dict[str, Any]] = Field(default_factory=list)
    trend: dict[str, Any] = Field(default_factory=dict)
    anomalies: dict[str, Any] = Field(default_factory=dict)


class InsightResult(BaseModel):
    text: str
    is_fallback: bool = False
    provider: str = "template"
    warning: str | None = None


class ReportModel(BaseModel):
    quality: DataQualityReport
    analysis: AnalysisResult
    anomalies: list[dict[str, Any]] = Field(default_factory=list)
    insight: str = ""
    insight_is_fallback: bool = False
    insight_provider: str = "template"
    generated_at: datetime
