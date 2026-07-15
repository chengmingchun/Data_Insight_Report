"""DeepSeek configuration page; values remain in the current Streamlit session."""

import streamlit as st

from src.config import AppConfig
from src.ui_state import initialize_session


st.set_page_config(page_title="AI Settings", page_icon=":material/settings:", layout="centered")
initialize_session(st.session_state, AppConfig())

st.title("AI Settings")
st.caption("配置仅保存在当前浏览器会话，不写入仓库、报告或日志。")

with st.form("deepseek_settings"):
    enabled = st.toggle("启用 DeepSeek 洞察", value=st.session_state.ai_enabled)
    provider = st.selectbox("Provider", options=["deepseek"], index=0, disabled=True)
    model = st.text_input("模型", value=st.session_state.llm_model)
    base_url = st.text_input("Base URL", value=st.session_state.llm_base_url)
    api_key = st.text_input(
        "API Key",
        value=st.session_state.llm_api_key,
        type="password",
        placeholder="sk-...",
    )
    timeout = st.number_input(
        "超时（秒）",
        min_value=1.0,
        max_value=120.0,
        value=float(st.session_state.llm_timeout_seconds),
        step=1.0,
    )
    saved = st.form_submit_button("保存当前会话配置", type="primary", width="stretch")

if saved:
    st.session_state.ai_enabled = enabled
    st.session_state.llm_provider = provider
    st.session_state.llm_model = model.strip() or "deepseek-v4-flash"
    st.session_state.llm_base_url = base_url.strip() or "https://api.deepseek.com"
    st.session_state.llm_api_key = api_key.strip()
    st.session_state.llm_timeout_seconds = timeout
    st.success("设置已保存到当前会话。回到分析工作台重新生成报告即可生效。")

st.page_link("app.py", label="返回分析工作台", icon=":material/arrow_back:")
