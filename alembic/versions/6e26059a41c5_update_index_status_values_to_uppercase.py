"""update_index_status_values_to_uppercase

Revision ID: 6e26059a41c5
Revises: 70fe164ab32a
Create Date: 2025-10-24 17:05:32.460378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e26059a41c5'
down_revision: Union[str, Sequence[str], None] = '70fe164ab32a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old CHECK constraint (lowercase values)
    op.drop_constraint('document_index_status_check', 'document', type_='check')

    # Update existing lowercase values to uppercase to match the enum
    op.execute("UPDATE document SET index_status = 'PENDING' WHERE index_status = 'pending'")
    op.execute("UPDATE document SET index_status = 'INDEXED' WHERE index_status = 'indexed'")
    op.execute("UPDATE document SET index_status = 'FAILED' WHERE index_status = 'failed'")

    # Recreate CHECK constraint with uppercase values
    op.create_check_constraint(
        'document_index_status_check',
        'document',
        "index_status IN ('PENDING', 'INDEXED', 'FAILED')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the uppercase CHECK constraint
    op.drop_constraint('document_index_status_check', 'document', type_='check')

    # Revert uppercase values back to lowercase
    op.execute("UPDATE document SET index_status = 'pending' WHERE index_status = 'PENDING'")
    op.execute("UPDATE document SET index_status = 'indexed' WHERE index_status = 'INDEXED'")
    op.execute("UPDATE document SET index_status = 'failed' WHERE index_status = 'FAILED'")

    # Recreate CHECK constraint with lowercase values
    op.create_check_constraint(
        'document_index_status_check',
        'document',
        "index_status IN ('pending', 'indexed', 'failed')"
    )
