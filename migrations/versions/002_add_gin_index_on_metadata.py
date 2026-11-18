"""add gin index on metadata

Revision ID: 002_add_gin_index_on_metadata
Revises: 001_create_documents_and_pages
Create Date: 2026-11-18 21:05:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_gin_index_on_metadata"
down_revision: Union[str, Sequence[str], None] = "001_create_documents_and_pages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_documents_metadata_gin",
        "documents",
        ["metadata"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"metadata": "jsonb_path_ops"},
    )


def downgrade() -> None:
    op.drop_index(
        "ix_documents_metadata_gin",
        table_name="documents",
        postgresql_using="gin",
        postgresql_ops={"metadata": "jsonb_path_ops"},
    )
