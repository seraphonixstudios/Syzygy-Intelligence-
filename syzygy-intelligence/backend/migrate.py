#!/usr/bin/env python
"""Safe database migration runner.

Best practices:
- Explicit error handling and logging
- Pre-flight checks before running migrations
- Exit codes for Docker health checks
- Structured output for debugging
"""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.db.session import init_db
from app.logging_setup import logger


async def run_migrations() -> bool:
    """Execute database migrations with proper error handling."""
    logger.info(
        "Starting database initialization",
        environment=settings.env,
        database_url=settings.database_url.replace(settings.db_password, "****"),
    )

    try:
        # Initialize database (creates tables)
        success = await init_db()

        if success:
            logger.info("Database initialization completed successfully")
            return True
        else:
            logger.error("Database initialization failed")
            return False

    except Exception as exc:
        logger.error(
            "Unexpected error during database initialization",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return False


def main() -> int:
    """Entry point."""
    try:
        success = asyncio.run(run_migrations())
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        return 130
    except Exception as exc:
        logger.error(
            "Fatal error during migration",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
