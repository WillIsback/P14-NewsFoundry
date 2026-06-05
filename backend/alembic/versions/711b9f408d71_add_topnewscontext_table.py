"""add_topnewscontext_table

Revision ID: 711b9f408d71
Revises: f112a69a9208
Create Date: 2026-06-01 11:49:56.093723

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '711b9f408d71'
down_revision: Union[str, Sequence[str], None] = 'f112a69a9208'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('topnewscontext',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('date', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('source_country', sqlmodel.sql.sqltypes.AutoString(length=2), nullable=False),
    sa.Column('language', sqlmodel.sql.sqltypes.AutoString(length=2), nullable=False),
    sa.Column('system_prompt', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('news', sa.JSON(), nullable=False),
    sa.Column('created_at', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chat.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topnewscontext_chat_id'), 'topnewscontext', ['chat_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_topnewscontext_chat_id'), table_name='topnewscontext')
    op.drop_table('topnewscontext')
