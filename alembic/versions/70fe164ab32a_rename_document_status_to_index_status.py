"""rename_document_status_to_index_status

Revision ID: 70fe164ab32a
Revises: a05529dbd2e0
Create Date: 2025-10-24 15:19:45.529956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70fe164ab32a'
down_revision: Union[str, Sequence[str], None] = 'a05529dbd2e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename the column from 'status' to 'index_status'
    op.alter_column('document', 'status', new_column_name='index_status')

    # Add CHECK constraint for enum values
    op.create_check_constraint(
        'document_index_status_check',
        'document',
        "index_status IN ('pending', 'indexed', 'failed')"
    )

    # Create index on index_status for better query performance
    op.create_index('ix_document_index_status', 'document', ['index_status'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the index
    op.drop_index('ix_document_index_status', table_name='document')

    # Drop the CHECK constraint
    op.drop_constraint('document_index_status_check', 'document', type_='check')

    # Rename the column back from 'index_status' to 'status'
    op.alter_column('document', 'index_status', new_column_name='status')
