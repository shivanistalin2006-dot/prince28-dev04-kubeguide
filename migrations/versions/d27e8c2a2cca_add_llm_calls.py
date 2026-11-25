"""add llm_calls

Revision ID: d27e8c2a2cca
Revises: 9ad28903e3bc
Create Date: 2026-11-25 13:38:58.064153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd27e8c2a2cca'
down_revision: Union[str, Sequence[str], None] = '9ad28903e3bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'llm_calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('model', sa.String(length=64), nullable=False),
        sa.Column('purpose', sa.String(length=32), server_default='chat', nullable=False),
        sa.Column('prompt_version', sa.String(length=32), server_default='v1', nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('tokens_in', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tokens_out', sa.Integer(), server_default='0', nullable=False),
        sa.Column('latency_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('cost_inr', sa.Numeric(precision=12, scale=6), server_default='0.0', nullable=False),
        sa.Column('fallback_used', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_llm_calls')),
    )
    op.create_index(op.f('ix_llm_calls_provider'), 'llm_calls', ['provider'], unique=False)
    op.create_index(op.f('ix_llm_calls_request_id'), 'llm_calls', ['request_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_llm_calls_request_id'), table_name='llm_calls')
    op.drop_index(op.f('ix_llm_calls_provider'), table_name='llm_calls')
    op.drop_table('llm_calls')
