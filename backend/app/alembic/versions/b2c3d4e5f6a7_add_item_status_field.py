"""add_item_status_field

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-14 13:00:00.000000

Adds a nullable ``status`` column to the ``item`` table (v1.1.1).
Default is NULL (existing rows unaffected) — application treats NULL as "active".
A future migration will backfill and add a NOT NULL constraint once confirmed safe.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_VALID_STATUSES = ("active", "archived", "deleted")


def upgrade() -> None:
    op.add_column(
        "item",
        sa.Column(
            "status",
            sqlmodel.AutoString(length=20),
            nullable=True,
            server_default=None,
            comment="Item lifecycle status (active|archived|deleted). NULL = active.",
        ),
    )
    op.create_index("ix_item_status", "item", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_item_status", table_name="item")
    op.drop_column("item", "status")
