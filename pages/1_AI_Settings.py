"""AI model configuration stored only in the current Streamlit session."""

import streamlit as st

from src.config import AppConfig
from src.ui_state import initialize_session


PROVIDER_PRESETS = {
    "DeepSeek": {
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
    },
    "OpenAI": {
        "provider": "openai",
        "model": "",
        "base_url": "https://api.openai.com/v1",
    },
    "OpenRouter": {
        "provider": "openrouter",
        "model": "",
        "base_url": "https://openrouter.ai/api/v1",
    },
    "Custom": {
        "provider": "custom",
        "model": "",
        "base_url": "",
    },
}


def apply_provider_preset() -> None:
    preset = PROVIDER_PRESETS[st.session_state.provider_preset]
    st.session_state.llm_provider = preset["provider"]
    if st.session_state.provider_preset != "Custom":
        st.session_state.llm_base_url = preset["base_url"]
        st.session_state.llm_model = preset["model"]


st.set_page_config(page_title="AI Settings", page_icon=":material/settings:", layout="centered")
initialize_session(st.session_state, AppConfig())

provider_labels = list(PROVIDER_PRESETS)
current_label = next(
    (
        label
        for label, preset in PROVIDER_PRESETS.items()
        if preset["provider"] == st.session_state.llm_provider
    ),
    "Custom",
)
st.session_state.setdefault("provider_preset", current_label)

st.title("AI Settings")
st.caption("配置仅保存在当前浏览器会话，不写入仓库、报告或日志。")

st.selectbox(
    "服务预设",
    options=provider_labels,
    key="provider_preset",
    on_change=apply_provider_preset,
)

with st.form("ai_settings"):
    enabled = st.toggle("启用 AI 洞察", value=st.session_state.ai_enabled)
    model = st.text_input(
        "模型名称",
        value=st.session_state.llm_model,
        placeholder="输入服务商支持的模型 ID",
    )
    base_url = st.text_input(
        "Base URL",
        value=st.session_state.llm_base_url,
        placeholder="https://example.com/v1",
    )
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
    if enabled and (not model.strip() or not base_url.strip() or not api_key.strip()):
        st.error("启用 AI 洞察时，请完整填写模型名称、Base URL 和 API Key。")
    else:
        preset = PROVIDER_PRESETS[st.session_state.provider_preset]
        st.session_state.ai_enabled = enabled
        st.session_state.llm_provider = preset["provider"]
        st.session_state.llm_model = model.strip()
        st.session_state.llm_base_url = base_url.strip()
        st.session_state.llm_api_key = api_key.strip()
        st.session_state.llm_timeout_seconds = timeout
        st.success("设置已保存到当前会话。返回分析工作台重新生成报告即可生效。")

st.page_link("app.py", label="返回分析工作台", icon=":material/arrow_back:")
