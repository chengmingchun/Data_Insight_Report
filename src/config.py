"""Application configuration and safe defaults."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Data Insight Report"
    max_upload_mb: int = Field(default=20, ge=1, le=100)
    top_n: int = Field(default=10, ge=1, le=50)
    enable_llm: bool = True
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-v4-flash"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_timeout_seconds: float = Field(default=30.0, ge=1, le=120)
