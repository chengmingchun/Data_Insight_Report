"""Offline HTML report rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from jinja2 import Environment, FileSystemLoader, select_autoescape

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
