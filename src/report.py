"""Offline HTML and PDF report rendering."""

from __future__ import annotations

from pathlib import Path
from io import BytesIO
from typing import Mapping
from xml.sax.saxutils import escape

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.graphics.shapes import Circle, Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.models import ReportModel


class HtmlReportGenerator:
    def __init__(self, template_path: Path) -> None:
        self.template_path = template_path
        self.environment = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def generate(self, report: ReportModel, chart_html: Mapping[str, str]) -> str:
        template = self.environment.get_template(self.template_path.name)
        return template.render(report=report, charts=dict(chart_html))


class PdfReportGenerator:
    """Generate a self-contained Chinese PDF without browser/system dependencies."""

    FONT = "STSong-Light"
    INK = colors.HexColor("#25313c")
    MUTED = colors.HexColor("#68747f")
    ACCENT = colors.HexColor("#167d76")
    WARM = colors.HexColor("#e0953e")
    SURFACE = colors.HexColor("#f5f7f7")

    def __init__(self) -> None:
        if self.FONT not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(UnicodeCIDFont(self.FONT))
        base = getSampleStyleSheet()
        self.styles = {
            "title": ParagraphStyle(
                "ChineseTitle", parent=base["Title"], fontName=self.FONT,
                fontSize=22, leading=29, textColor=self.INK, alignment=TA_CENTER,
            ),
            "heading": ParagraphStyle(
                "ChineseHeading", parent=base["Heading2"], fontName=self.FONT,
                fontSize=14, leading=20, textColor=self.INK, spaceBefore=8, spaceAfter=8,
            ),
            "body": ParagraphStyle(
                "ChineseBody", parent=base["BodyText"], fontName=self.FONT,
                fontSize=9.5, leading=15, textColor=self.INK,
            ),
            "small": ParagraphStyle(
                "ChineseSmall", parent=base["BodyText"], fontName=self.FONT,
                fontSize=8, leading=12, textColor=self.MUTED,
            ),
        }

    def generate(self, report: ReportModel) -> bytes:
        output = BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=17 * mm,
            bottomMargin=16 * mm,
            title="AI 数据洞察分析报告",
            author="AI Data Insight Report",
        )
        story = self._build_story(report)
        document.build(story, onFirstPage=self._draw_page, onLaterPages=self._draw_page)
        return output.getvalue()

    def _build_story(self, report: ReportModel) -> list[object]:
        overview = report.analysis.overview
        story: list[object] = [
            Paragraph("AI 数据洞察分析报告", self.styles["title"]),
            Paragraph(
                f"生成时间：{report.generated_at:%Y-%m-%d %H:%M:%S}",
                self.styles["small"],
            ),
            Spacer(1, 7 * mm),
            Paragraph("业务概览", self.styles["heading"]),
            self._table(
                [
                    ["有效订单", "总销售额（元）", "平均订单金额（元）", "退款率"],
                    [
                        f"{overview.valid_orders:,}",
                        f"{overview.total_sales:,.2f}",
                        f"{overview.average_order_value:,.2f}",
                        f"{overview.refund_rate:.2%}",
                    ],
                ],
                [42 * mm, 46 * mm, 48 * mm, 36 * mm],
            ),
            Spacer(1, 5 * mm),
            Paragraph("数据洞察", self.styles["heading"]),
            Paragraph(escape(report.insight).replace("\n", "<br/>"), self.styles["body"]),
            Spacer(1, 4 * mm),
            Paragraph("说明：洞察仅解释程序计算出的结构化统计结果，不参与数值计算。", self.styles["small"]),
            Spacer(1, 5 * mm),
            Paragraph("数据质量", self.styles["heading"]),
            self._table(
                [
                    ["原始记录", "完全有效", "部分有效", "拒绝记录", "重复记录"],
                    [
                        report.quality.raw_rows,
                        report.quality.valid_rows,
                        report.quality.partial_rows,
                        report.quality.rejected_rows,
                        report.quality.duplicate_rows,
                    ],
                ],
                [34.4 * mm] * 5,
            ),
            PageBreak(),
            Paragraph("图表分析", self.styles["heading"]),
            KeepTogether([
                Paragraph("每日销售额趋势", self.styles["body"]),
                self._line_chart(report.analysis.daily_sales),
            ]),
            Spacer(1, 4 * mm),
            KeepTogether([
                Paragraph("商品销售额 Top-N", self.styles["body"]),
                self._bar_chart(report.analysis.top_products, "product", self.WARM),
            ]),
            Spacer(1, 4 * mm),
            KeepTogether([
                Paragraph("地区销售额", self.styles["body"]),
                self._bar_chart(report.analysis.sales_by_region, "region", self.ACCENT),
            ]),
            PageBreak(),
            Paragraph("商品 Top-N", self.styles["heading"]),
            self._top_products_table(report),
            Spacer(1, 6 * mm),
            Paragraph("需关注记录", self.styles["heading"]),
            self._anomaly_table(report),
            Spacer(1, 6 * mm),
            Paragraph("数据处理规则", self.styles["heading"]),
        ]
        story.extend(
            Paragraph(f"• {escape(rule)}", self.styles["small"])
            for rule in report.quality.applied_rules
        )
        return story

    def _table(self, rows: list[list[object]], widths: list[float]) -> Table:
        table = Table(rows, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), self.FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), self.SURFACE),
            ("TEXTCOLOR", (0, 0), (-1, -1), self.INK),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dfe5e8")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        return table

    def _top_products_table(self, report: ReportModel) -> Table:
        rows: list[list[object]] = [["商品", "销售额（元）", "销量", "订单数"]]
        rows.extend([
            [row["product"], f'{float(row["sales"]):,.2f}', row["quantity"], row["orders"]]
            for row in report.analysis.top_products
        ])
        if len(rows) == 1:
            rows.append(["暂无数据", "-", "-", "-"])
        return self._table(rows, [69 * mm, 42 * mm, 30 * mm, 31 * mm])

    def _anomaly_table(self, report: ReportModel) -> Table:
        rows: list[list[object]] = [["订单", "源行", "类型", "原因", "金额（元）"]]
        rows.extend([
            [
                str(row.get("order_id") or "-"),
                str(row.get("source_row") or "-"),
                str(row.get("anomaly_type") or "-"),
                Paragraph(escape(str(row.get("anomaly_reason") or "-")), self.styles["small"]),
                f'{float(row.get("sales_amount") or 0):,.2f}',
            ]
            for row in report.anomalies[:30]
        ])
        if len(rows) == 1:
            rows.append(["-", "-", "-", "未发现异常", "-"])
        return self._table(rows, [34 * mm, 20 * mm, 25 * mm, 65 * mm, 28 * mm])

    def _bar_chart(self, rows: list[dict], label_key: str, color: colors.Color) -> Drawing:
        drawing = Drawing(500, 150)
        values = [float(row.get("sales", 0)) for row in rows[:8]]
        if not values or max(values) <= 0:
            drawing.add(String(190, 70, "暂无可展示数据", fontName=self.FONT, fontSize=10))
            return drawing
        maximum = max(values)
        bar_width = min(48, 410 / len(values))
        for index, (row, value) in enumerate(zip(rows[:8], values)):
            x = 48 + index * bar_width
            height = 95 * value / maximum
            drawing.add(Rect(x, 28, bar_width - 8, height, fillColor=color, strokeColor=None))
            label = str(row.get(label_key, ""))[:8]
            drawing.add(String(x, 13, label, fontName=self.FONT, fontSize=6.5))
            drawing.add(String(x, min(137, 31 + height), f"{value:,.0f}", fontName=self.FONT, fontSize=6))
        drawing.add(Line(42, 28, 480, 28, strokeColor=self.MUTED, strokeWidth=0.5))
        return drawing

    def _line_chart(self, rows: list[dict]) -> Drawing:
        drawing = Drawing(500, 150)
        values = [float(row.get("sales", 0)) for row in rows]
        if not values:
            drawing.add(String(190, 70, "暂无可展示数据", fontName=self.FONT, fontSize=10))
            return drawing
        low, high = min(values), max(values)
        span = high - low or 1
        step = 420 / max(1, len(values) - 1)
        points = [(48 + index * step, 34 + (value - low) / span * 90) for index, value in enumerate(values)]
        drawing.add(Line(42, 28, 480, 28, strokeColor=self.MUTED, strokeWidth=0.5))
        for index, ((x, y), row) in enumerate(zip(points, rows)):
            if index:
                previous = points[index - 1]
                drawing.add(Line(previous[0], previous[1], x, y, strokeColor=self.ACCENT, strokeWidth=2))
            drawing.add(Circle(x, y, 2.5, fillColor=self.ACCENT, strokeColor=None))
            if len(rows) <= 12 or index in (0, len(rows) - 1):
                drawing.add(String(x - 12, 14, str(row.get("date", ""))[5:], fontName=self.FONT, fontSize=6))
        return drawing

    def _draw_page(self, canvas, document) -> None:
        canvas.saveState()
        canvas.setStrokeColor(self.ACCENT)
        canvas.setLineWidth(1.5)
        canvas.line(16 * mm, A4[1] - 11 * mm, A4[0] - 16 * mm, A4[1] - 11 * mm)
        canvas.setFont(self.FONT, 7.5)
        canvas.setFillColor(self.MUTED)
        canvas.drawRightString(A4[0] - 16 * mm, 9 * mm, f"第 {document.page} 页")
        canvas.restoreState()
