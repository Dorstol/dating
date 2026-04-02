"""add telegram_id to users

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-04-02 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_users_telegram_id", "users", ["telegram_id"]
    )

    # Allow nullable for Telegram users who haven't completed profile yet
    op.alter_column("users", "gender", nullable=True)
    op.alter_column("users", "age", nullable=True)
    op.alter_column("users", "location", nullable=True)


def downgrade() -> None:
    op.alter_column("users", "location", nullable=False)
    op.alter_column("users", "age", nullable=False)
    op.alter_column("users", "gender", nullable=False)
    op.drop_constraint("uq_users_telegram_id", "users", type_="unique")
    op.drop_column("users", "telegram_id")
