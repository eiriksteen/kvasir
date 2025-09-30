"""Update function in pipeline to use args

Revision ID: 66a9f61aa0cf
Revises: 9ca5afd2a9ea
Create Date: 2025-09-24 23:36:40.210305

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66a9f61aa0cf'
down_revision: Union[str, None] = '9ca5afd2a9ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('function_in_pipeline', 'config',
                    new_column_name='args', schema='pipeline')


def downgrade() -> None:
    op.alter_column('function_in_pipeline', 'config',
                    new_column_name='args', schema='pipeline')
