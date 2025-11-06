"""Remove input_variable and output_variable from analysis_result

Revision ID: a1b2c3d4e5f6
Revises: 33375276a937
Create Date: 2025-11-05 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '33375276a937'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop input_variable and output_variable columns from analysis_result table
    op.drop_column('analysis_result', 'input_variable', schema='analysis')
    op.drop_column('analysis_result', 'output_variable', schema='analysis')


def downgrade() -> None:
    # Re-add the columns if we need to rollback
    op.add_column('analysis_result', sa.Column('output_variable', sa.String(), nullable=True), schema='analysis')
    op.add_column('analysis_result', sa.Column('input_variable', sa.String(), nullable=True), schema='analysis')

