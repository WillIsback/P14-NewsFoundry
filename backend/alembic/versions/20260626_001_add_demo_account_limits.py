"""add_demo_account_limits_to_user

Revision ID: 20260626001
Revises: dcc84e175202
Create Date: 2026-06-26 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260626001"
down_revision: Union[str, Sequence[str], None] = "dcc84e175202"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — add demo account limit fields to user table."""
    op.add_column(
        "user",
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column(
            "worldnews_calls_used",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "user",
        sa.Column("worldnews_calls_limit", sa.Integer(), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column(
            "llm_tokens_in_used",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "llm_tokens_out_used",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "user",
        sa.Column("llm_tokens_limit", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema — remove demo account limit fields from user table."""
    op.drop_column("user", "llm_tokens_limit")
    op.drop_column("user", "llm_tokens_out_used")
    op.drop_column("user", "llm_tokens_in_used")
    op.drop_column("user", "worldnews_calls_limit")
    op.drop_column("user", "worldnews_calls_used")
    op.drop_column("user", "expires_at")
