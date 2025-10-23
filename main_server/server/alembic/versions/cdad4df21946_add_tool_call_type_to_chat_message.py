"""Add tool call type to chat message

Revision ID: cdad4df21946
Revises: 0a486f7b6bc6
Create Date: 2025-10-23 15:26:20.466154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cdad4df21946'
down_revision: Union[str, None] = '0a486f7b6bc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
