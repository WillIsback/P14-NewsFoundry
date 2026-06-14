"""add_loaded_articles_to_chat

Revision ID: dcc84e175202
Revises: a1b2c3d4e5f6
Create Date: 2026-06-14 17:29:15.266295

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dcc84e175202"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "chat",
        sa.Column("loaded_articles", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("chat", "loaded_articles")
