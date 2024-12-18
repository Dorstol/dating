"""add photo for user

Revision ID: fbe8e7b83af7
Revises: e36e1847b744
Create Date: 2024-12-18 14:24:40.351264

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fbe8e7b83af7"
down_revision: Union[str, None] = "e36e1847b744"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users", sa.Column("photo", sa.String(length=255), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "photo")
    # ### end Alembic commands ###
