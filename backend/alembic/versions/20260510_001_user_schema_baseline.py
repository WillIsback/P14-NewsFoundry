"""Create or align user schema.

Revision ID: 20260510_001
Revises:
Create Date: 2026-05-10 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260510_001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


USER_ROLE_ENUM = sa.Enum("ADMIN", "USER", name="userrole")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    USER_ROLE_ENUM.create(bind, checkfirst=True)

    if not inspector.has_table("user"):
        op.create_table(
            "user",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("role", USER_ROLE_ENUM, nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_user_email", "user", ["email"], unique=True)
        op.create_index("ix_user_role", "user", ["role"], unique=False)
        return

    columns = {column["name"] for column in inspector.get_columns("user")}
    if "role" not in columns:
        op.add_column(
            "user",
            sa.Column(
                "role",
                USER_ROLE_ENUM,
                nullable=False,
                server_default=sa.text("'USER'"),
            ),
        )
        op.alter_column("user", "role", server_default=None)

    indexes = {index["name"] for index in inspector.get_indexes("user")}
    unique_constraints = inspector.get_unique_constraints("user")
    has_unique_email = any(
        set(constraint.get("column_names") or []) == {"email"}
        for constraint in unique_constraints
    )

    if "ix_user_email" not in indexes and not has_unique_email:
        op.create_index("ix_user_email", "user", ["email"], unique=True)

    if "ix_user_role" not in indexes:
        op.create_index("ix_user_role", "user", ["role"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("user"):
        indexes = {index["name"] for index in inspector.get_indexes("user")}
        if "ix_user_role" in indexes:
            op.drop_index("ix_user_role", table_name="user")

        columns = {column["name"] for column in inspector.get_columns("user")}
        if "role" in columns:
            op.drop_column("user", "role")

    USER_ROLE_ENUM.drop(bind, checkfirst=True)
