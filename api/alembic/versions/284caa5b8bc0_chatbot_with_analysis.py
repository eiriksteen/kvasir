"""chatbot with analysis

Revision ID: 284caa5b8bc0
Revises: 8b1f64068c37
Create Date: 2025-04-24 19:11:01.349194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '284caa5b8bc0'
down_revision: Union[str, None] = '8b1f64068c37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analysis_context table
    op.create_table(
        'analysis_context',
        sa.Column('context_id', sa.UUID(), nullable=False),
        sa.Column('analysis_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['context_id'], ['chat.context.id'], ),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis.analysis_jobs_results.job_id'], ),
        sa.PrimaryKeyConstraint('context_id', 'analysis_id'),
        schema='chat'
    )

    # Add primary key constraints to existing tables
    # op.drop_constraint('dataset_context_pkey', 'dataset_context', schema='chat', type_='primary')
    op.create_primary_key('dataset_context_pkey', 'dataset_context', ['context_id', 'dataset_id'], schema='chat')

    # op.drop_constraint('automation_context_pkey', 'automation_context', schema='chat', type_='primary')
    op.create_primary_key('automation_context_pkey', 'automation_context', ['context_id', 'automation_id'], schema='chat')


def downgrade() -> None:
    op.drop_table('analysis_context', schema='chat')

    op.drop_constraint('dataset_context_pkey', 'dataset_context', schema='chat', type_='primary')
    # op.create_primary_key('dataset_context_pkey', 'dataset_context', ['context_id', 'dataset_id'], schema='chat')

    op.drop_constraint('automation_context_pkey', 'automation_context', schema='chat', type_='primary')
    # op.create_primary_key('automation_context_pkey', 'automation_context', ['context_id', 'automation_id'], schema='chat')
