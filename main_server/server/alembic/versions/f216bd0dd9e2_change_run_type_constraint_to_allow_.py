"""Change run type constraint to allow model integration

Revision ID: f216bd0dd9e2
Revises: 0996c0a49520
Create Date: 2025-09-22 18:05:26.336542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f216bd0dd9e2'
down_revision: Union[str, None] = '0996c0a49520'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing constraint
    op.drop_constraint('type_check', 'run', schema='runs', type_='check')
    # Add the updated constraint with 'model_integration'
    op.create_check_constraint(
        'type_check',
        'run',
        "type IN ('data_integration', 'analysis', 'pipeline', 'swe', 'data_source_analysis', 'model_integration')",
        schema='runs'
    )


def downgrade() -> None:
    # Drop the updated constraint
    op.drop_constraint('type_check', 'run', schema='runs', type_='check')
    # Revert to the old constraint without 'model_integration'
    op.create_check_constraint(
        'type_check',
        'run',
        "type IN ('data_integration', 'analysis', 'pipeline', 'swe', 'data_source_analysis')",
        schema='runs'
    )
