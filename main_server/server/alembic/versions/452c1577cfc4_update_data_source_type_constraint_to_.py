"""update_data_source_type_constraint_to_file

Revision ID: 452c1577cfc4
Revises: 7053500a7d92
Create Date: 2025-09-05 13:14:17.758971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '452c1577cfc4'
down_revision: Union[str, None] = '7053500a7d92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing constraint that allows 'TabularFile'
    op.execute(
        'ALTER TABLE data_sources.data_source DROP CONSTRAINT IF EXISTS data_source_type_check')

    # Add new constraint that allows 'file'
    op.create_check_constraint(
        'data_source_type_check',
        'data_source',
        "type IN ('file')",
        schema='data_sources'
    )


def downgrade() -> None:
    # Drop the new constraint that allows 'file'
    op.execute(
        'ALTER TABLE data_sources.data_source DROP CONSTRAINT IF EXISTS data_source_type_check')

    # Add back the old constraint that allows 'TabularFile'
    op.create_check_constraint(
        'data_source_type_check',
        'data_source',
        "type IN ('TabularFile')",
        schema='data_sources'
    )
