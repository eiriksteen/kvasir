"""empty message

Revision ID: dc32e77d0d99
Revises: 61ebf35a7cbe, 8dd53662563e
Create Date: 2025-10-27 01:39:28.269462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc32e77d0d99'
down_revision: Union[str, None] = ('61ebf35a7cbe', '8dd53662563e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
