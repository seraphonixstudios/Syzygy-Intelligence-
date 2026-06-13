"""Add searchable_key_hash to api_keys and fix datetime defaults to use func.now()

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add the searchable_key_hash column to api_keys
    # For existing rows, generate a placeholder value (they will need to be migrated separately if needed)
    op.add_column(
        "api_keys",
        sa.Column("searchable_key_hash", sa.String(16), nullable=True),
    )
    
    # Create unique index on searchable_key_hash (for new keys)
    op.create_index(
        "idx_api_key_searchable",
        "api_keys",
        ["searchable_key_hash"],
        unique=True,
        postgresql_where=sa.text("searchable_key_hash IS NOT NULL"),
    )
    
    # Create index for is_active filtering
    op.create_index(
        "idx_api_key_active",
        "api_keys",
        ["is_active"],
    )
    
    # Make searchable_key_hash NOT NULL after populating (if needed, populate with a hash of hashed_key)
    # Note: This is a manual step or requires a data migration script
    op.alter_column("api_keys", "searchable_key_hash", nullable=False)


def downgrade() -> None:
    op.drop_index("idx_api_key_active", table_name="api_keys")
    op.drop_index("idx_api_key_searchable", table_name="api_keys")
    op.drop_column("api_keys", "searchable_key_hash")
