"""Explainable statistical anomaly detection."""

from __future__ import annotations

import pandas as pd

from src.models import AnomalyResult


class IqrAnomalyDetector:
    def __init__(self, multiplier: float = 1.5, min_samples: int = 4) -> None:
        self.multiplier = multiplier
        self.min_samples = min_samples

    def detect(self, clean_df: pd.DataFrame) -> AnomalyResult:
        completed = clean_df.loc[clean_df["status"].eq("已完成")].copy()
        if len(completed) < self.min_samples:
            return AnomalyResult()

        q1 = float(completed["sales_amount"].quantile(0.25))
        q3 = float(completed["sales_amount"].quantile(0.75))
        iqr = q3 - q1
        lower = q1 - self.multiplier * iqr
        upper = q3 + self.multiplier * iqr
        outliers = completed.loc[
            completed["sales_amount"].lt(lower) | completed["sales_amount"].gt(upper)
        ]
        records = []
        for row in outliers.to_dict("records"):
            records.append(
                {
                    "order_id": row["order_id"],
                    "source_row": row.get("source_row"),
                    "sales_amount": round(float(row["sales_amount"]), 2),
                    "anomaly_reason": f"IQR 范围外（{lower:.2f} ~ {upper:.2f}）",
                    "anomaly_type": "statistical",
                }
            )
        return AnomalyResult(
            records=records,
            lower_bound=round(lower, 2),
            upper_bound=round(upper, 2),
        )
