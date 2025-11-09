"""Rename image url to path

Revision ID: 4df294a88305
Revises: 6fda224b2243
Create Date: 2025-11-06 18:42:28.808772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4df294a88305'
down_revision: Union[str, None] = '6fda224b2243'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('image', 'image_url',
                    new_column_name='image_path', schema='visualization')


def downgrade() -> None:
    op.alter_column('image', 'image_path',
                    new_column_name='image_url', schema='visualization')
