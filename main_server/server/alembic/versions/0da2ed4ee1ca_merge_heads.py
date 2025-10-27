"""merge_heads

Revision ID: 0da2ed4ee1ca
Revises: 254b30ce4bcd, cdad4df21946
Create Date: 2025-10-24 10:21:03.600389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0da2ed4ee1ca'
down_revision: Union[str, None] = ('254b30ce4bcd', 'cdad4df21946')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
