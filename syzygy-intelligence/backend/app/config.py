"""Syzygy Configuration — loaded from env vars with pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class SyzygyConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SYZYGY_",
        extra="ignore",
    )

    # General
    env: Literal["development", "production", "testing"] = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-to-a-random-secret"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "syzygy"
    db_user: str = "syzygy"
    db_password: str = "syzygy_secret"
    db_sqlite_path: str = str(Path("./data/syzygy.db").absolute())

    def model_post_init(self, __context):
        """Validate configuration after initialization."""
        if self.env == "production" and self.secret_key == "change-me-to-a-random-secret":
            raise ValueError(
                "SYZYGY_SECRET_KEY must be set to a secure random value in production. "
                "Generate one with: openssl rand -hex 32"
            )

    @property
    def database_url(self) -> str:
        if self.env == "development":
            return f"sqlite+aiosqlite:///{self.db_sqlite_path}"
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        if self.env == "development":
            return f"sqlite:///{self.db_sqlite_path}"
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def db_is_sqlite(self) -> bool:
        return self.env == "development"

    @property
    def allowed_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string. Warns if empty in production."""
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if not origins and self.env == "production":
            from app.logging_setup import logger
            logger.warning("CORS origins list is empty in production. No cross-origin requests will be allowed.")
        return origins

    # Auth
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    oauth_redirect_url: str = "http://localhost:8000/api/auth/oauth"

    # Free tier & trial
    free_tier_days: int = 14
    free_tier_monthly_messages: int = 100
    premium_monthly_messages: int = 10000

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "syzygy_secret"

    # Chroma
    chroma_path: str = str(Path("./data/chroma").absolute())

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "qwen3:8b-gpu"
    critic_model: str = "qwen3:8b-gpu"
    synthesis_model: str = "qwen3:8b-gpu"
    coding_model: str = "qwen3:8b-gpu"
    creative_model: str = "dolphin-llama3:8b-gpu"
    vision_model: str = "llava:13b-gpu"
    gpu_model: str = "qwen3:8b-gpu"
    fast_model: str = "dolphin-llama3:8b-gpu"

    # LiteLLM Fallback
    litellm_enabled: bool = False
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    fallback_model: str = "gpt-4o-mini"

    # Consensus Engine
    max_consensus_rounds: int = 6
    min_consensus_rounds: int = 2
    convergence_threshold: float = 0.85
    variance_threshold: float = 0.1

    # Execution
    sandbox_docker_image: str = "syzygy-sandbox:latest"
    sandbox_timeout: int = 120
    sandbox_memory_limit: str = "512m"

    # Uploads
    upload_dir: str = str(Path("./data/uploads").absolute())
    max_upload_size_mb: int = 10

    # Paths
    data_dir: str = str(Path("./data").absolute())

    @property
    def sync_database_url(self) -> str:
        return self.database_url_sync


settings = SyzygyConfig()
