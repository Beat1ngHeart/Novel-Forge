"""add chapter parse_source

Revision ID: 8914be71377d
Revises: bc2d7ce34516
Create Date: 2026-06-23 15:33:16.168387

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "8914be71377d"
down_revision: Union[str, Sequence[str], None] = "bc2d7ce34516"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chapters", sa.Column("parse_source", sa.String(length=20), server_default="auto"))
    op.execute("UPDATE chapters SET parse_source = 'auto' WHERE parse_source IS NULL")


def downgrade() -> None:
    op.drop_column("chapters", "parse_source")
