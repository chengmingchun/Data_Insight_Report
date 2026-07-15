"""Streamlit session configuration without persistence."""

from __future__ import annotations

from typing import Any, MutableMapping

from src.config import AppConfig


SESSION_DEFAULTS = {
    "ai_enabled": True,
    "llm_provider": "deepseek",
    "llm_model": "deepseek-v4-flash",
    "llm_base_url": "https://api.deepseek.com",
    "llm_api_key": "",
    "llm_timeout_seconds": 30.0,
}


def initialize_session(state: MutableMapping[str, Any], config: AppConfig) -> None:
    defaults = {
        **SESSION_DEFAULTS,
        "ai_enabled": config.enable_llm,
        "llm_provider": config.llm_provider,
        "llm_model": config.llm_model,
        "llm_base_url": config.llm_base_url,
        "llm_api_key": config.llm_api_key,
        "llm_timeout_seconds": config.llm_timeout_seconds,
    }
    for key, value in defaults.items():
        state.setdefault(key, value)


def config_from_session(state: MutableMapping[str, Any], config: AppConfig) -> AppConfig:
    return config.model_copy(
        update={
            "enable_llm": bool(state["ai_enabled"]),
            "llm_provider": str(state["llm_provider"]),
            "llm_model": str(state["llm_model"]),
            "llm_base_url": str(state["llm_base_url"]),
            "llm_api_key": str(state["llm_api_key"]),
            "llm_timeout_seconds": float(state["llm_timeout_seconds"]),
        }
    )
