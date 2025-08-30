"""Add user id to pipeline

Revision ID: cecefa0f2f78
Revises: 467773eb8e40
Create Date: 2025-08-20 16:08:09.750613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cecefa0f2f78'
down_revision: Union[str, None] = '467773eb8e40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
