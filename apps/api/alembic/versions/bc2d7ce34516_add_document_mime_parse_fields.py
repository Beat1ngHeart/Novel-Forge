"""add document mime parse fields

Revision ID: bc2d7ce34516
Revises: 14a093ee0542
Create Date: 2026-06-23 15:16:26.071909

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "bc2d7ce34516"
down_revision: Union[str, Sequence[str], None] = "14a093ee0542"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("source_documents", sa.Column("mime_type", sa.String(length=100), server_default="text/plain"))
    op.add_column("source_documents", sa.Column("parse_status", sa.String(length=20), server_default="pending"))
    op.add_column("source_documents", sa.Column("error_message", sa.Text(), server_default=""))
    # Backfill existing rows
    op.execute("UPDATE source_documents SET mime_type = 'text/plain' WHERE mime_type IS NULL")
    op.execute("UPDATE source_documents SET parse_status = 'pending' WHERE parse_status IS NULL")
    op.execute("UPDATE source_documents SET error_message = '' WHERE error_message IS NULL")


def downgrade() -> None:
    op.drop_column("source_documents", "error_message")
    op.drop_column("source_documents", "parse_status")
    op.drop_column("source_documents", "mime_type")
