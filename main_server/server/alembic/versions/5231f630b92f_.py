"""empty message

Revision ID: 5231f630b92f
Revises: 051729d13101, dc32e77d0d99
Create Date: 2025-10-27 16:58:58.234121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5231f630b92f'
down_revision: Union[str, None] = ('051729d13101', 'dc32e77d0d99')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
