"""Add time fields to viz

Revision ID: 26e65198551f
Revises: 4df294a88305
Create Date: 2025-11-06 18:51:15.394568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26e65198551f'
down_revision: Union[str, None] = '4df294a88305'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created_at and updated_at columns to echart table
    op.add_column('echart', sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False), schema='visualization')

    # Add created_at and updated_at columns to image table
    op.add_column('image', sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False), schema='visualization')

    # Add created_at and updated_at columns to table table
    op.add_column('table', sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False), schema='visualization')


def downgrade() -> None:
    # Remove created_at and updated_at columns from table table
    op.drop_column('table', 'updated_at', schema='visualization')
    op.drop_column('table', 'created_at', schema='visualization')

    # Remove created_at and updated_at columns from image table
    op.drop_column('image', 'updated_at', schema='visualization')
    op.drop_column('image', 'created_at', schema='visualization')

    # Remove created_at and updated_at columns from echart table
    op.drop_column('echart', 'updated_at', schema='visualization')
    op.drop_column('echart', 'created_at', schema='visualization')
