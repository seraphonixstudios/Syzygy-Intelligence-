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

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "syzygy"
    db_user: str = "syzygy"
    db_password: str = "syzygy_secret"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

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
    default_model: str = "qwen3.5:8b"
    critic_model: str = "deepseek-r1:7b"
    synthesis_model: str = "qwen3.5:8b"
    coding_model: str = "qwen-coder:7b"
    creative_model: str = "dolphin-llama3:8b"

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

    # Paths
    data_dir: str = str(Path("./data").absolute())

    @property
    def sync_database_url(self) -> str:
        return self.database_url_sync


settings = SyzygyConfig()
