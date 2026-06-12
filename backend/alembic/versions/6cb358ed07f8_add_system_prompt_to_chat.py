"""add_system_prompt_to_chat

Revision ID: 6cb358ed07f8
Revises: 711b9f408d71
Create Date: 2026-06-05 09:38:59.601504

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6cb358ed07f8"
down_revision: Union[str, Sequence[str], None] = "711b9f408d71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("chat", sa.Column("system_prompt", sa.TEXT(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("chat", "system_prompt")
