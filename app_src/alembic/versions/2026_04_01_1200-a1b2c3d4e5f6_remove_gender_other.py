"""remove gender other

Revision ID: a1b2c3d4e5f6
Revises: dc8995e00842
Create Date: 2026-04-01 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "dc8995e00842"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Remove users with gender 'Other' or set them to a default
    # before altering the enum (adjust as needed for your data)
    # Convert to VARCHAR first so we can safely update values
    op.execute("ALTER TABLE users ALTER COLUMN gender TYPE VARCHAR")
    op.execute("UPDATE users SET gender = 'Male' WHERE gender = 'Other'")
    op.execute("DROP TYPE IF EXISTS genderenum")
    op.execute("CREATE TYPE genderenum AS ENUM ('Male', 'Female')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN gender TYPE genderenum USING gender::genderenum"
    )
    op.execute("ALTER TABLE users ALTER COLUMN gender SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN gender TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS genderenum")
    op.execute("CREATE TYPE genderenum AS ENUM ('Male', 'Female', 'Other')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN gender TYPE genderenum USING gender::genderenum"
    )
