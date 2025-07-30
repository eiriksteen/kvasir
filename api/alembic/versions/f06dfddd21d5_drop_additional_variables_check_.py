"""drop_additional_variables_check_constraint

Revision ID: f06dfddd21d5
Revises: b317f7d96f1c
Create Date: 2025-07-29 17:05:02.287894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f06dfddd21d5'
down_revision: Union[str, None] = 'b317f7d96f1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the check constraint on additional_variables
    op.drop_constraint('data_object_additional_variables_check',
                       'data_object', schema='data_objects', type_='check')


def downgrade() -> None:
    # Recreate the check constraint on additional_variables
    op.create_check_constraint(
        'data_object_additional_variables_check',
        'data_object',
        "additional_variables IS NULL OR jsonb_typeof(additional_variables) = 'object'",
        schema='data_objects'
    )
