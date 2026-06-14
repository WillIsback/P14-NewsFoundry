"""Add press_review columns to chat table

Revision ID: a1b2c3d4e5f6
Revises: 6cb358ed07f8
Create Date: 2026-06-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6cb358ed07f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat",
        sa.Column(
            "press_review_title", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    op.add_column(
        "chat",
        sa.Column(
            "press_review_summary", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    op.add_column(
        "chat",
        sa.Column(
            "press_review_articles", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    op.add_column(
        "chat",
        sa.Column(
            "press_review_date", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_column("chat", "press_review_date")
    op.drop_column("chat", "press_review_articles")
    op.drop_column("chat", "press_review_summary")
    op.drop_column("chat", "press_review_title")
