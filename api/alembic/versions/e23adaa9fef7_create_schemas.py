"""create_schemas

Revision ID: e23adaa9fef7
Revises: 
Create Date: 2025-07-31 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e23adaa9fef7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all schemas
    op.execute('CREATE SCHEMA IF NOT EXISTS auth')
    op.execute('CREATE SCHEMA IF NOT EXISTS data_sources')
    op.execute('CREATE SCHEMA IF NOT EXISTS runs')
    op.execute('CREATE SCHEMA IF NOT EXISTS orchestrator')
    op.execute('CREATE SCHEMA IF NOT EXISTS data_objects')
    op.execute('CREATE SCHEMA IF NOT EXISTS analysis')
    op.execute('CREATE SCHEMA IF NOT EXISTS automation')
    op.execute('CREATE SCHEMA IF NOT EXISTS project')
    op.execute('CREATE SCHEMA IF NOT EXISTS node')


def downgrade() -> None:
    # Drop all schemas
    op.execute('DROP SCHEMA IF EXISTS node CASCADE')
    op.execute('DROP SCHEMA IF EXISTS project CASCADE')
    op.execute('DROP SCHEMA IF EXISTS automation CASCADE')
    op.execute('DROP SCHEMA IF EXISTS analysis CASCADE')
    op.execute('DROP SCHEMA IF EXISTS data_objects CASCADE')
    op.execute('DROP SCHEMA IF EXISTS orchestrator CASCADE')
    op.execute('DROP SCHEMA IF EXISTS runs CASCADE')
    op.execute('DROP SCHEMA IF EXISTS data_sources CASCADE')
    op.execute('DROP SCHEMA IF EXISTS auth CASCADE')
