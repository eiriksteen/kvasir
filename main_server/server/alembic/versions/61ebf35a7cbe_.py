"""empty message

Revision ID: 61ebf35a7cbe
Revises: 449f3106dcaf
Create Date: 2025-10-27 01:31:05.034651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61ebf35a7cbe'
down_revision: Union[str, None] = '449f3106dcaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
