"""Remove order from fn inp/out

Revision ID: f0016774b7a0
Revises: 6a789adaab75
Create Date: 2025-09-12 15:44:49.216609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0016774b7a0'
down_revision: Union[str, None] = '6a789adaab75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
