"""add blocks and reports

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-01 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create report reason enum via raw SQL to avoid duplicate type errors
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE reportreasonenum AS ENUM "
        "('Spam', 'Fake', 'Harassment', 'Inappropriate Content'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$"
    )

    # Create blocks table
    op.create_table(
        "blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "blocked_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "blocked_user_id"),
    )

    # Create reports table using raw SQL for the reason column
    # to avoid SQLAlchemy auto-creating the enum type
    op.execute("""
        CREATE TABLE reports (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reported_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reason reportreasonenum NOT NULL,
            description VARCHAR(500),
            created_at TIMESTAMP DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("blocks")
    sa.Enum(name="reportreasonenum").drop(op.get_bind(), checkfirst=True)
