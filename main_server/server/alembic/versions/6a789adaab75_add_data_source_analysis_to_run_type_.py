"""Add data_source_analysis to run type check constraint

Revision ID: 6a789adaab75
Revises: 452c1577cfc4
Create Date: 2025-09-09 20:49:21.378902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a789adaab75'
down_revision: Union[str, None] = '452c1577cfc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing check constraint
    op.drop_constraint('type_check', 'run', schema='runs', type_='check')
    # Create the updated check constraint with data_source_analysis using PostgreSQL ARRAY syntax
    op.execute("""
        ALTER TABLE runs.run ADD CONSTRAINT type_check
        CHECK (type = ANY(ARRAY['data_integration', 'analysis', 'pipeline', 'swe', 'data_source_analysis']))
    """)


def downgrade() -> None:
    # Drop the updated check constraint
    op.drop_constraint('type_check', 'run', schema='runs', type_='check')
    # Recreate the original check constraint without data_source_analysis using PostgreSQL ARRAY syntax
    op.execute("""
        ALTER TABLE runs.run ADD CONSTRAINT type_check
        CHECK (type = ANY(ARRAY['data_integration', 'analysis', 'pipeline', 'swe']))
    """)
