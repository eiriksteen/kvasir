"""replace_linked_list_with_order_field

Revision ID: 27e22eacdf28
Revises: f36a7b4421c9
Create Date: 2025-10-21 21:16:09.933625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27e22eacdf28'
down_revision: Union[str, None] = 'f36a7b4421c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
