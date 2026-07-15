"""Business metrics calculated only from accepted deterministic data."""

from __future__ import annotations

import pandas as pd

from src.models import AnalysisResult, OverviewMetrics


class DataAnalyzer:
    def __init__(self, top_n: int = 10) -> None:
        self.top_n = top_n

    def analyze(self, clean_df: pd.DataFrame) -> AnalysisResult:
        frame = clean_df.copy(deep=True)
        if frame.empty:
            return AnalysisResult()

        completed = frame.loc[frame["status"].eq("已完成")].copy()
        refunded_orders = int(frame.loc[frame["status"].eq("已退款"), "order_id"].nunique())
        valid_orders = int(frame["order_id"].nunique())
        completed_orders = int(completed["order_id"].nunique())
        total_sales = round(float(completed["sales_amount"].sum()), 2)

        overview = OverviewMetrics(
            valid_orders=valid_orders,
            total_sales=total_sales,
            average_order_value=round(total_sales / completed_orders, 2) if completed_orders else 0.0,
            total_quantity=int(completed["quantity"].sum()),
            refunded_orders=refunded_orders,
            refund_rate=refunded_orders / valid_orders if valid_orders else 0.0,
        )

        sales_by_region = self._sales_group(completed, "region")
        sales_by_category = self._sales_group(completed, "category")
        sales_by_product = self._product_group(completed)
        orders_by_status = (
            frame.groupby("status", dropna=False)["order_id"]
            .nunique()
            .rename("orders")
            .reset_index()
            .sort_values(["orders", "status"], ascending=[False, True])
            .to_dict("records")
        )
        daily_sales = self._daily_sales(completed)

        pivot = completed.pivot_table(
            index="region",
            columns="category",
            values="sales_amount",
            aggfunc="sum",
            fill_value=0,
        )
        region_category_matrix = pivot.reset_index().to_dict("records") if not pivot.empty else []

        return AnalysisResult(
            overview=overview,
            sales_by_region=sales_by_region,
            sales_by_category=sales_by_category,
            sales_by_product=sales_by_product,
            orders_by_status=orders_by_status,
            daily_sales=daily_sales,
            top_products=sales_by_product[: self.top_n],
            top_products_by_quantity=sorted(
                sales_by_product,
                key=lambda row: (-int(row["quantity"]), str(row["product"])),
            )[: self.top_n],
            top_regions=sales_by_region[: min(self.top_n, 5)],
            top_categories=sales_by_category[: min(self.top_n, 5)],
            region_category_matrix=region_category_matrix,
        )

    @staticmethod
    def _sales_group(frame: pd.DataFrame, dimension: str) -> list[dict[str, object]]:
        if frame.empty:
            return []
        result = (
            frame.groupby(dimension, dropna=False)
            .agg(sales=("sales_amount", "sum"), orders=("order_id", "nunique"))
            .reset_index()
            .sort_values(["sales", dimension], ascending=[False, True])
        )
        result["sales"] = result["sales"].round(2)
        return result.to_dict("records")

    @staticmethod
    def _product_group(frame: pd.DataFrame) -> list[dict[str, object]]:
        if frame.empty:
            return []
        result = (
            frame.groupby("product", dropna=False)
            .agg(sales=("sales_amount", "sum"), quantity=("quantity", "sum"), orders=("order_id", "nunique"))
            .reset_index()
            .sort_values(["sales", "product"], ascending=[False, True])
        )
        result["sales"] = result["sales"].round(2)
        return result.to_dict("records")

    @staticmethod
    def _daily_sales(frame: pd.DataFrame) -> list[dict[str, object]]:
        dated = frame.dropna(subset=["order_date"])
        if dated.empty:
            return []
        result = (
            dated.assign(date=dated["order_date"].dt.strftime("%Y-%m-%d"))
            .groupby("date", as_index=False)["sales_amount"]
            .sum()
            .rename(columns={"sales_amount": "sales"})
            .sort_values("date")
        )
        result["sales"] = result["sales"].round(2)
        return result.to_dict("records")
