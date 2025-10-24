"""add_viewport_to_project

Revision ID: 449f3106dcaf
Revises: 0da2ed4ee1ca
Create Date: 2025-10-24 10:21:09.122758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '449f3106dcaf'
down_revision: Union[str, None] = '0da2ed4ee1ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add viewport columns to project table
    op.add_column('project', sa.Column('view_port_x', sa.Float(), nullable=False, server_default='0.0'), schema='project')
    op.add_column('project', sa.Column('view_port_y', sa.Float(), nullable=False, server_default='0.0'), schema='project')
    op.add_column('project', sa.Column('view_port_zoom', sa.Float(), nullable=False, server_default='1.0'), schema='project')


def downgrade() -> None:
    # Remove viewport columns from project table
    op.drop_column('project', 'view_port_zoom', schema='project')
    op.drop_column('project', 'view_port_y', schema='project')
    op.drop_column('project', 'view_port_x', schema='project')
