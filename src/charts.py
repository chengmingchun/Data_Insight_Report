"""Plotly figures built from precomputed analysis DTOs."""

from __future__ import annotations

import plotly.graph_objects as go

from src.models import AnalysisResult


ACCENT = "#167d76"
WARM = "#e0953e"
INK = "#25313c"


class ChartBuilder:
    def build_all(self, result: AnalysisResult) -> dict[str, go.Figure]:
        return {
            "daily_sales": self.build_daily_sales_chart(result),
            "top_products": self.build_top_products_chart(result),
            "region_sales": self.build_region_sales_chart(result),
        }

    def build_daily_sales_chart(self, result: AnalysisResult) -> go.Figure:
        rows = result.daily_sales
        figure = go.Figure(
            go.Scatter(
                x=[row["date"] for row in rows],
                y=[row["sales"] for row in rows],
                mode="lines+markers",
                line={"color": ACCENT, "width": 3},
                marker={"size": 7},
                hovertemplate="日期 %{x}<br>销售额 ¥%{y:,.2f}<extra></extra>",
            )
        )
        return self._finish(figure, "每日销售额趋势", "日期", "销售额（元）", empty=not rows)

    def build_top_products_chart(self, result: AnalysisResult) -> go.Figure:
        rows = list(reversed(result.top_products))
        figure = go.Figure(
            go.Bar(
                x=[row["sales"] for row in rows],
                y=[row["product"] for row in rows],
                orientation="h",
                marker_color=WARM,
                hovertemplate="%{y}<br>销售额 ¥%{x:,.2f}<extra></extra>",
            )
        )
        return self._finish(figure, "商品销售额 Top-N", "销售额（元）", "商品", empty=not rows)

    def build_region_sales_chart(self, result: AnalysisResult) -> go.Figure:
        rows = result.sales_by_region
        figure = go.Figure(
            go.Bar(
                x=[row["region"] for row in rows],
                y=[row["sales"] for row in rows],
                marker_color=ACCENT,
                hovertemplate="%{x}<br>销售额 ¥%{y:,.2f}<extra></extra>",
            )
        )
        return self._finish(figure, "各地区销售额", "地区", "销售额（元）", empty=not rows)

    @staticmethod
    def _finish(
        figure: go.Figure,
        title: str,
        x_title: str,
        y_title: str,
        *,
        empty: bool,
    ) -> go.Figure:
        figure.update_layout(
            title=title,
            xaxis_title=x_title,
            yaxis_title=y_title,
            template="plotly_white",
            colorway=[ACCENT, WARM, INK],
            height=390,
            margin={"l": 40, "r": 24, "t": 60, "b": 45},
            font={"family": "Arial, Microsoft YaHei, sans-serif", "color": INK},
            separators=".,",
        )
        if empty:
            figure.add_annotation(
                text="当前口径下没有可展示数据",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
            )
        return figure
