"""Streamlit analysis workbench; all business logic lives in src modules."""

from __future__ import annotations

from io import BytesIO
import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import AppConfig
from src.exceptions import DataReportError
from src.insight import InsightProviderFactory
from src.orchestrator import AnalysisOptions, AnalysisOrchestrator, PipelineResult
from src.ui_state import config_from_session, initialize_session


ROOT = Path(__file__).resolve().parent
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


st.set_page_config(
    page_title="AI Data Insight Report",
    page_icon=":material/analytics:",
    layout="wide",
)


def run_analysis(file_bytes: bytes, filename: str, top_n: int, config: AppConfig) -> PipelineResult:
    provider = InsightProviderFactory.create(config)
    return AnalysisOrchestrator(insight_provider=provider).run(
        BytesIO(file_bytes),
        filename=filename,
        options=AnalysisOptions(top_n=top_n, max_upload_mb=config.max_upload_mb),
    )


def render_result(result: PipelineResult) -> None:
    report = result.report
    overview = report.analysis.overview

    st.subheader("数据概览")
    metric_columns = st.columns(6)
    metric_columns[0].metric("原始记录", f"{report.quality.raw_rows:,}")
    metric_columns[1].metric("有效订单", f"{overview.valid_orders:,}")
    metric_columns[2].metric("总销售额", f"¥{overview.total_sales:,.2f}")
    metric_columns[3].metric("平均订单金额", f"¥{overview.average_order_value:,.2f}")
    metric_columns[4].metric("退款率", f"{overview.refund_rate:.2%}")
    metric_columns[5].metric("需关注记录", f"{overview.anomaly_count:,}")

    st.subheader("AI 洞察")
    st.write(report.insight)
    st.caption("AI 洞察仅用于辅助解释；所有统计数字均由确定性程序计算。")

    quality_tab, charts_tab, matrix_tab, anomaly_tab = st.tabs(
        ["数据质量", "图表分析", "多维分析", "异常记录"]
    )
    with quality_tab:
        quality_columns = st.columns(4)
        quality_columns[0].metric("完全有效", report.quality.valid_rows)
        quality_columns[1].metric("部分有效", report.quality.partial_rows)
        quality_columns[2].metric("拒绝记录", report.quality.rejected_rows)
        quality_columns[3].metric("重复记录", report.quality.duplicate_rows)

        invalid = pd.DataFrame(
            [
                {"异常类型": key, "数量": value}
                for key, value in report.quality.invalid_counts.items()
                if value
            ]
        )
        if not invalid.empty:
            st.dataframe(invalid, width="stretch", hide_index=True)
        with st.expander("查看清洗规则"):
            for rule in report.quality.applied_rules:
                st.write(f"- {rule}")
        if not result.rejected_df.empty:
            st.dataframe(result.rejected_df, width="stretch", hide_index=True)

    with charts_tab:
        st.plotly_chart(result.figures["daily_sales"], width="stretch")
        left, right = st.columns(2)
        left.plotly_chart(result.figures["top_products"], width="stretch")
        right.plotly_chart(result.figures["region_sales"], width="stretch")

    with matrix_tab:
        matrix = pd.DataFrame(report.analysis.region_category_matrix)
        if matrix.empty:
            st.info("当前没有可生成透视表的已完成订单。")
        else:
            st.dataframe(matrix, width="stretch", hide_index=True)

    with anomaly_tab:
        if result.anomaly_df.empty:
            st.success("未发现规则异常或 IQR 统计异常。")
        else:
            st.dataframe(result.anomaly_df, width="stretch", hide_index=True)

    st.subheader("导出")
    download_columns = st.columns(4)
    download_columns[0].download_button(
        "下载 HTML 报告",
        data=result.html.encode("utf-8"),
        file_name="data_insight_report.html",
        mime="text/html",
        width="stretch",
    )
    download_columns[1].download_button(
        "下载 PDF 报告",
        data=result.pdf,
        file_name="data_insight_report.pdf",
        mime="application/pdf",
        width="stretch",
    )
    download_columns[2].download_button(
        "下载清洗后 CSV",
        data=result.clean_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="clean_orders.csv",
        mime="text/csv",
        width="stretch",
    )
    download_columns[3].download_button(
        "下载异常记录 CSV",
        data=result.anomaly_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="anomalies.csv",
        mime="text/csv",
        width="stretch",
        disabled=result.anomaly_df.empty,
    )


config = AppConfig()
initialize_session(st.session_state, config)

st.title("AI Data Insight Report")
st.caption("电商订单 CSV 的可追踪清洗、确定性统计、异常检测与智能洞察")

with st.sidebar:
    st.header("分析参数")
    uploaded = st.file_uploader("上传订单 CSV", type=["csv"])
    use_sample = st.checkbox("使用内置样例数据", value=False)
    top_n = st.slider("Top-N", min_value=3, max_value=20, value=config.top_n)
    st.page_link("pages/1_AI_Settings.py", label="AI Settings", icon=":material/settings:")
    generate = st.button("生成报告", type="primary", width="stretch")

if generate:
    try:
        if uploaded is not None and not use_sample:
            content = uploaded.getvalue()
            filename = uploaded.name
        elif use_sample:
            sample = ROOT / "data" / "sample_orders.csv"
            content = sample.read_bytes()
            filename = sample.name
        else:
            content = b""
            filename = "upload.csv"

        if not content:
            st.warning("请上传 CSV 或启用内置样例数据。")
        else:
            with st.spinner("正在执行清洗、统计与报告生成..."):
                session_config = config_from_session(st.session_state, config)
                st.session_state.pipeline_result = run_analysis(content, filename, top_n, session_config)
    except DataReportError as exc:
        st.error(str(exc))
    except Exception:
        LOGGER.exception("Unexpected analysis failure")
        st.error("分析失败，请检查 CSV 格式或应用日志。")

if "pipeline_result" in st.session_state:
    render_result(st.session_state.pipeline_result)
else:
    st.info("请上传 CSV 并点击“生成报告”，或手动启用内置样例数据。")
