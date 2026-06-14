"""Syzygy Configuration — loaded from env vars with pydantic-settings.

Best practices:
- Separation of concerns: validation logic decoupled from initialization
- Type safety: explicit types for all configuration values
- Security: secrets validation at startup, not runtime
- Observability: structured logging for config parsing errors
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Lazy import to break circular dependency with logging_setup.py
# logging_setup imports settings from this module at module level.
def _get_logger():
    try:
        from app.logging_setup import logger
        return logger
    except ImportError:
        import logging
        return logging.getLogger("syzygy.config")


class DatabaseConfig:
    """Encapsulate database configuration parsing."""

    @staticmethod
    def parse_database_url(raw_url: str) -> dict[str, Any]:
        """Parse DATABASE_URL and return config dict."""
        pattern = (
            r"(?:postgresql|postgresql\+asyncpg)://"
            r"(?P<user>[^:]+):(?P<pass>[^@]+)@"
            r"(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>.+)"
        )
        match = re.match(pattern, raw_url)
        if not match:
            raise ValueError(f"Invalid DATABASE_URL format: {raw_url}")

        return {
            "db_user": match.group("user"),
            "db_password": match.group("pass"),
            "db_host": match.group("host"),
            "db_port": int(match.group("port")) if match.group("port") else 5432,
            "db_name": match.group("db"),
        }


class SyzygyConfig(BaseSettings):
    """Application configuration with validation and type safety."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SYZYGY_",
        extra="ignore",
        validate_assignment=True,
    )

    # ──── General ────
    env: Literal["development", "production", "testing"] = Field(
        default="development",
        description="Environment mode",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log output format (json or text)")
    secret_key: str = Field(
        default="change-me-to-a-random-secret",
        description="JWT signing key (must be randomized in production)",
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated CORS origins",
    )

    # ──── Database ────
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="syzygy", description="Database name")
    db_user: str = Field(default="syzygy", description="Database user")
    db_password: str = Field(default="syzygy_secret", description="Database password")
    db_sqlite_path: str = Field(
        default_factory=lambda: str(Path("./data/syzygy.db").absolute()),
        description="SQLite database file path",
    )

    # ──── Auth ────
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=60, description="Access token TTL")
    refresh_token_expire_days: int = Field(default=30, description="Refresh token TTL")

    # ──── OAuth ────
    google_client_id: str = Field(default="", description="Google OAuth client ID")
    google_client_secret: str = Field(default="", description="Google OAuth client secret")
    github_client_id: str = Field(default="", description="GitHub OAuth client ID")
    github_client_secret: str = Field(default="", description="GitHub OAuth client secret")
    oauth_redirect_url: str = Field(
        default="http://localhost:8001/api/auth/oauth",
        description="OAuth callback URL",
    )

    # ──── Billing ────
    free_tier_days: int = Field(default=14, description="Free trial duration")
    free_tier_monthly_messages: int = Field(default=100, description="Free tier message limit")
    premium_monthly_messages: int = Field(default=10000, description="Premium message limit")

    # ──── Redis ────
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # ──── Neo4j ────
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="syzygy_secret", description="Neo4j password")

    # ──── Vector DB ────
    chroma_path: str = Field(
        default_factory=lambda: str(Path("./data/chroma").absolute()),
        description="Chroma vector DB path",
    )

    # ──── LLM Models ────
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    default_model: str = Field(default="qwen3:8b-gpu", description="Default LLM model")
    critic_model: str = Field(default="qwen3:8b-gpu", description="Critic agent model")
    synthesis_model: str = Field(default="qwen3:8b-gpu", description="Synthesis model")
    coding_model: str = Field(default="qwen3:8b-gpu", description="Code generation model")
    creative_model: str = Field(default="qwen3:8b-gpu", description="Creative writing model")
    vision_model: str = Field(default="llava:13b-gpu", description="Vision model")
    gpu_model: str = Field(default="qwen3:8b-gpu", description="GPU-optimized model")
    fast_model: str = Field(default="qwen3:8b-gpu", description="Fast inference model")

    # ──── LiteLLM Fallback ────
    litellm_enabled: bool = Field(default=False, description="Enable LiteLLM fallback")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    fallback_model: str = Field(default="gpt-4o-mini", description="Fallback LLM model")

    # ──── Consensus Engine ────
    max_consensus_rounds: int = Field(default=6, description="Maximum consensus iterations")
    min_consensus_rounds: int = Field(default=2, description="Minimum consensus iterations")
    convergence_threshold: float = Field(default=0.85, description="Consensus convergence threshold")
    variance_threshold: float = Field(default=0.1, description="Variance threshold")
    consensus_timeout: float = Field(default=600.0, description="Consensus engine timeout (seconds)")
    multi_model_timeout: float = Field(default=120.0, description="Multi-model query timeout (seconds)")

    # ──── Sandbox Execution ────
    sandbox_docker_image: str = Field(default="syzygy-sandbox:latest", description="Sandbox image")
    sandbox_timeout: int = Field(default=120, description="Sandbox execution timeout (seconds)")
    sandbox_memory_limit: str = Field(default="512m", description="Sandbox memory limit")

    # ──── File Uploads ────
    upload_dir: str = Field(
        default_factory=lambda: str(Path("./data/uploads").absolute()),
        description="Upload directory",
    )
    max_upload_size_mb: int = Field(default=10, description="Max upload size (MB)")

    # ──── Data Paths ────
    data_dir: str = Field(
        default_factory=lambda: str(Path("./data").absolute()),
        description="Data directory root",
    )

    # ──── Email ────
    email_provider: str = Field(
        default="console",
        description="Email provider (console, sendgrid, ses)",
    )
    sendgrid_api_key: str = Field(default="", description="SendGrid API key")
    ses_region: str = Field(default="us-east-1", description="AWS SES region")
    ses_access_key_id: str = Field(default="", description="AWS access key")
    ses_secret_access_key: str = Field(default="", description="AWS secret key")
    email_from_address: str = Field(default="noreply@syzygy.local", description="From email")
    email_from_name: str = Field(default="Syzygy Intelligence", description="From name")

    # ──── Rate Limiting ────
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_second: float = Field(default=10.0, description="Rate limit (req/sec)")
    rate_limit_burst: int = Field(default=20, description="Rate limit burst size")
    rate_limit_authenticated_per_second: float = Field(default=30.0, description="Authenticated rate limit")
    rate_limit_authenticated_burst: int = Field(default=60, description="Authenticated burst size")

    # ──── Payments ────
    stripe_secret_key: str = Field(default="", description="Stripe secret key")
    stripe_publishable_key: str = Field(default="", description="Stripe publishable key")
    stripe_webhook_secret: str = Field(default="", description="Stripe webhook secret")
    stripe_premium_price_id: str = Field(default="price_premium_monthly", description="Premium price ID")
    stripe_enterprise_price_id: str = Field(default="price_enterprise_monthly", description="Enterprise price ID")

    # ──── API ────
    api_key_length: int = Field(default=48, description="API key length")

    @field_validator("rate_limit_per_second", "rate_limit_authenticated_per_second")
    @classmethod
    def validate_positive_float(cls, v: float) -> float:
        """Ensure rate limits are positive."""
        if v <= 0:
            raise ValueError("Rate limit must be positive")
        return v

    @field_validator("rate_limit_burst", "rate_limit_authenticated_burst")
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        """Ensure burst sizes are positive."""
        if v <= 0:
            raise ValueError("Burst size must be positive")
        return v

    def __init__(self, **data: Any) -> None:
        """Initialize and validate configuration."""
        # Parse DATABASE_URL env var if present (takes precedence)
        raw_url = os.environ.get("DATABASE_URL", "")
        if raw_url:
            try:
                db_config = DatabaseConfig.parse_database_url(raw_url)
                data.update(db_config)
                _get_logger().info(
                    "Parsed DATABASE_URL",
                    host=db_config["db_host"],
                    port=db_config["db_port"],
                    database=db_config["db_name"],
                )
            except ValueError as e:
                _get_logger().error("Failed to parse DATABASE_URL", error=str(e))
                raise

        super().__init__(**data)

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        # Production-only validations
        if self.env == "production":
            self._validate_production_secrets()
            self._validate_production_cors()
            self._validate_production_email()

    def _validate_production_secrets(self) -> None:
        """Validate all secrets are set in production."""
        errors: list[str] = []

        if self.secret_key == "change-me-to-a-random-secret":
            errors.append("SYZYGY_SECRET_KEY must be set to a random value (generate with: openssl rand -hex 32)")

        if self.db_password == "syzygy_secret":
            errors.append("SYZYGY_DB_PASSWORD must be set to a secure value")

        if self.neo4j_password == "syzygy_secret":
            errors.append("SYZYGY_NEO4J_PASSWORD must be set to a secure value")

        if errors:
            error_msg = "Production configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            _get_logger().error("Production secrets not configured", details="\n".join(errors))
            raise ValueError(error_msg)

        _get_logger().info("Production secrets validated")

    def _validate_production_cors(self) -> None:
        """Warn if CORS origins contain localhost."""
        if "localhost" in self.cors_origins:
            _get_logger().warning(
                "CORS origins contain localhost in production",
                detail="Set SYZYGY_CORS_ORIGINS to your actual domain(s)",
            )

        if "localhost" in self.oauth_redirect_url:
            _get_logger().warning(
                "OAuth redirect URL contains localhost in production",
                detail="OAuth providers will not recognize redirect",
            )

    def _validate_production_email(self) -> None:
        """Warn if email not configured for production."""
        if self.email_provider == "console":
            _get_logger().warning(
                "Email provider is 'console' in production",
                detail="Email tokens will be exposed in API responses. "
                "Configure SendGrid or AWS SES instead.",
            )

    @property
    def database_url(self) -> str:
        """Get async database URL."""
        if self.env == "development":
            return f"sqlite+aiosqlite:///{self.db_sqlite_path}"
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Get sync database URL for migrations."""
        if self.env == "development":
            return f"sqlite:///{self.db_sqlite_path}"
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def effective_log_format(self) -> str:
        """Get effective log format (JSON in production, text in dev)."""
        return "json" if self.env == "production" or self.log_format == "json" else "text"

    @property
    def db_is_sqlite(self) -> bool:
        """Check if using SQLite (development only)."""
        return self.env == "development" and "sqlite" in self.database_url

    @property
    def allowed_origins(self) -> list[str]:
        """Parse and validate CORS origins."""
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if not origins:
            if self.env == "production":
                # In production, require explicit CORS configuration
                _get_logger().error("CORS origins list is empty in production — requests will be blocked")
                raise ValueError(
                    "SYZYGY_CORS_ORIGINS must be set to valid domain(s) in production. "
                    "Set via environment variable: SYZYGY_CORS_ORIGINS=https://your-domain.com"
                )
            # In development, allow localhost
            origins = ["http://localhost:3000", "http://localhost:8000"]
            _get_logger().info("CORS origins empty, using development defaults", origins=origins)
        return origins

    @property
    def frontend_url(self) -> str:
        """Get primary frontend URL."""
        origins = self.allowed_origins
        return origins[0] if origins else "http://localhost:3000"


# Global settings instance — created at module import
settings = SyzygyConfig()
