"""add_tags_and_item_tag_link

Revision ID: a1b2c3d4e5f6
Revises: 1a31ce608336
Create Date: 2026-09-14 12:00:00.000000

Adds the ``tag`` and ``itemtaglink`` tables introduced in v1.1.0.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "1a31ce608336"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- tag table ---
    op.create_table(
        "tag",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column("color", sqlmodel.AutoString(length=7), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tag_name"), "tag", ["name"], unique=False)

    # --- itemtaglink join table ---
    op.create_table(
        "itemtaglink",
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["item.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("item_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("itemtaglink")
    op.drop_index(op.f("ix_tag_name"), table_name="tag")
    op.drop_table("tag")
