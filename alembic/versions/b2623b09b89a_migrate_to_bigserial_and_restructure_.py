"""migrate_to_bigserial_and_restructure_predictions

Revision ID: b2623b09b89a
Revises: df372993474c
Create Date: 2025-10-30 20:06:07.887520

This migration changes:
1. All ID columns from VARCHAR/UUID to BIGSERIAL (auto-incrementing BIGINT)
2. Removes model_path and vectorizer_path from model table (generated dynamically)
3. Removes model_id from prediction table, adds model_version INTEGER
4. Updates all foreign keys to use BIGINT

NOTE: This is a breaking change. All existing data will be lost.
No backward compatibility is maintained.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Identity


# revision identifiers, used by Alembic.
revision: str = 'b2623b09b89a'
down_revision: Union[str, Sequence[str], None] = 'df372993474c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to BIGSERIAL IDs and restructured predictions.

    WARNING: This will drop all existing tables and recreate them.
    All data will be lost.
    """
    # Drop all existing tables (in reverse order of dependencies)
    op.execute("DROP TABLE IF EXISTS prediction CASCADE")
    op.execute("DROP TABLE IF EXISTS document_label CASCADE")
    op.execute("DROP TABLE IF EXISTS model CASCADE")
    op.execute("DROP TABLE IF EXISTS field_class CASCADE")
    op.execute("DROP TABLE IF EXISTS task CASCADE")
    op.execute("DROP TABLE IF EXISTS field CASCADE")
    op.execute("DROP TABLE IF EXISTS document CASCADE")
    op.execute("DROP TABLE IF EXISTS project CASCADE")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS indexstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS modelstatus CASCADE")

    # Recreate tables with BIGSERIAL IDs

    # Project table
    op.create_table('project',
        sa.Column('id', sa.BigInteger(), Identity(start=1, cycle=False), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('index_status', sa.String(length=50), nullable=True),
        sa.Column('model_status', sa.String(length=50), nullable=True),
        sa.Column('last_trained_at', sa.DateTime(), nullable=True),
        sa.Column('last_indexed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_project'))
    )

    # Document table
    op.create_table('document',
        sa.Column('id', sa.BigInteger(), Identity(start=1, cycle=False), nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('content_path', sa.String(length=512), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('index_status', sa.Enum('NOT_INDEXED', 'PENDING', 'INDEXED', 'FAILED', name='indexstatus', native_enum=False, length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], name=op.f('fk_document_project_id_project'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_document'))
    )
    op.create_index(op.f('ix_document_project_id'), 'document', ['project_id'], unique=False)

    # Field table
    op.create_table('field',
        sa.Column('id', sa.BigInteger(), Identity(start=1, cycle=False), nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], name=op.f('fk_field_project_id_project'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_field'))
    )
    op.create_index(op.f('ix_field_project_id'), 'field', ['project_id'], unique=False)

    # Task table
    op.create_table('task',
        sa.Column('id', sa.BigInteger(), Identity(start=1, cycle=False), nullable=False),
        sa.Column('project_id', sa.BigInteger(), nullable=False),
        sa.Column('celery_id', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], name=op.f('fk_task_project_id_project'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_task'))
    )
    op.create_index(op.f('ix_task_celery_id'), 'task', ['celery_id'], unique=True)
    op.create_index(op.f('ix_task_project_id'), 'task', ['project_id'], unique=False)

    # FieldClass table
    op.create_table('field_class',
        sa.Column('id', sa.BigInteger(), Identity(start=1, cycle=False), nullable=False),
        sa.Column('field_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['field_id'], ['field.id'], name=op.f('fk_field_class_field_id_field'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_field_class'))
    )
    op.create_index(op.f('ix_field_class_field_id'), 'field_class', ['field_id'], unique=False)

    # Model table (without model_path and vectorizer_path)
    op.create_table('model',
        sa.Column('id', sa.BigInteger(), Identity(start=1, cycle=False), nullable=False),
        sa.Column('field_id', sa.BigInteger(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('TRAINING', 'READY', 'FAILED', name='modelstatus', native_enum=False, length=50), nullable=False),
        sa.Column('trained_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['field_id'], ['field.id'], name=op.f('fk_model_field_id_field'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_model'))
    )
    op.create_index(op.f('ix_model_field_id'), 'model', ['field_id'], unique=False)

    # DocumentLabel table
    op.create_table('document_label',
        sa.Column('id', sa.BigInteger(), Identity(start=1, cycle=False), nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('field_id', sa.BigInteger(), nullable=False),
        sa.Column('class_id', sa.BigInteger(), nullable=False),
        sa.Column('is_training_data', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['class_id'], ['field_class.id'], name=op.f('fk_document_label_class_id_field_class'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], name=op.f('fk_document_label_document_id_document'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['field.id'], name=op.f('fk_document_label_field_id_field'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_document_label')),
        sa.UniqueConstraint('document_id', 'field_id', name='uq_document_field_label')
    )
    op.create_index(op.f('ix_document_label_class_id'), 'document_label', ['class_id'], unique=False)
    op.create_index(op.f('ix_document_label_document_id'), 'document_label', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_label_field_id'), 'document_label', ['field_id'], unique=False)

    # Prediction table (without model_id, with model_version)
    op.create_table('prediction',
        sa.Column('id', sa.BigInteger(), Identity(start=1, cycle=False), nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('field_id', sa.BigInteger(), nullable=False),
        sa.Column('class_id', sa.BigInteger(), nullable=False),
        sa.Column('model_version', sa.Integer(), nullable=False, comment='Model version used for this prediction'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['class_id'], ['field_class.id'], name=op.f('fk_prediction_class_id_field_class'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], name=op.f('fk_prediction_document_id_document'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['field.id'], name=op.f('fk_prediction_field_id_field'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_prediction')),
        sa.UniqueConstraint('document_id', 'field_id', name='uq_document_field_prediction')
    )
    op.create_index(op.f('ix_prediction_class_id'), 'prediction', ['class_id'], unique=False)
    op.create_index(op.f('ix_prediction_document_id'), 'prediction', ['document_id'], unique=False)
    op.create_index(op.f('ix_prediction_field_id'), 'prediction', ['field_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema.

    WARNING: No backward compatibility. This will drop all tables.
    """
    # Drop all tables (in reverse order of dependencies)
    op.drop_table('prediction')
    op.drop_table('document_label')
    op.drop_table('model')
    op.drop_table('field_class')
    op.drop_table('task')
    op.drop_table('field')
    op.drop_table('document')
    op.drop_table('project')
