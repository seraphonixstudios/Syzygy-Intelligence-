"""add user table

Revision ID: 0001
Revises:
Create Date: 2026-06-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_superuser", sa.Boolean, default=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_reset_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message_count", sa.Integer, default=0),
        sa.Column("subscription_tier", sa.String(20), default="free"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("settings", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_user_email", "users", ["email"])


def downgrade() -> None:
    op.drop_index("idx_user_email", table_name="users")
    op.drop_table("users")
