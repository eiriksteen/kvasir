"""merge heads

Revision ID: 051729d13101
Revises: 449f3106dcaf, 8dd53662563e
Create Date: 2025-10-27 11:22:00.015232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '051729d13101'
down_revision: Union[str, None] = ('449f3106dcaf', '8dd53662563e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
