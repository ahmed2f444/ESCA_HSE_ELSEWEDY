from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_env: str = "development"
    app_timezone: str = "Africa/Cairo"

    database_url: str = ""
    database_name: str = "railway"
    db_host: str = "zephyr.proxy.rlwy.net"
    db_port: int = 17885
    db_name: str = "railway"
    db_user: str = "root"
    db_password: str = ""

    mysql_url: str = Field(default="", validation_alias="MYSQL_URL")
    mysql_host: str = Field(default="", validation_alias="MYSQLHOST")
    mysql_port: int = Field(default=17885, validation_alias="MYSQLPORT")
    mysql_user: str = Field(default="", validation_alias="MYSQLUSER")
    mysql_password: str = Field(default="", validation_alias="MYSQLPASSWORD")
    mysql_database: str = Field(default="", validation_alias="MYSQLDATABASE")

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-120b"

    # Local LLM fallback (Ollama)
    local_llm_enabled: bool = True
    local_llm_base_url: str = "http://localhost:11434/v1"
    local_llm_model: str = "esca-agent-local"

    # Spring Boot Integration (for mutations / automation)
    spring_api_base_url: str = "http://localhost:8080"
    automation_client_id: str = "esca-hse-automation"
    automation_client_secret: str = "local-automation-secret-change-me"
    spring_automation_client_id: str = "esca-hse-automation"
    spring_automation_client_secret: SecretStr = SecretStr("local-automation-secret-change-me")
    spring_connect_timeout_seconds: float = 3.0
    spring_read_timeout_seconds: float = 10.0
    spring_max_attempts: int = 3
    spring_token_refresh_leeway_seconds: int = 30

    automation_delivery_mode: Literal["dry_run", "spring"] = "dry_run"
    automation_live_enabled: bool = False
    enable_scheduler: bool = True

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )


settings = Settings()


@lru_cache
def get_settings() -> Settings:
    return settings
