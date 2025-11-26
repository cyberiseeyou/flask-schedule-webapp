"""Add employee import fields (simple)

Revision ID: add_employee_import_fields_simple
Revises: add_rejected_simple
Create Date: 2025-11-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_employee_import_fields_simple'
down_revision = 'add_rejected_simple'
branch_labels = None
depends_on = None


def upgrade():
    # Add new employee import fields using direct operations
    # SQLite supports ADD COLUMN directly
    try:
        op.add_column('employees', sa.Column('mv_retail_employee_number', sa.String(length=50), nullable=True))
    except Exception:
        pass  # Column may already exist

    try:
        op.add_column('employees', sa.Column('crossmark_employee_id', sa.String(length=50), nullable=True))
    except Exception:
        pass  # Column may already exist

    # Add indexes
    try:
        op.create_index('ix_employees_mv_retail_employee_number', 'employees', ['mv_retail_employee_number'], unique=False)
    except Exception:
        pass  # Index may already exist

    # Add unique index for crossmark_employee_id (acts like unique constraint in SQLite)
    try:
        op.create_index('uq_employees_crossmark_employee_id', 'employees', ['crossmark_employee_id'], unique=True)
    except Exception:
        pass  # Index may already exist

    # Try to create case-insensitive name index (may already exist)
    try:
        op.create_index('ix_employee_name_lower', 'employees', [sa.text('lower(name)')], unique=False)
    except Exception:
        pass  # Index already exists


def downgrade():
    # Remove case-insensitive name index
    try:
        op.drop_index('ix_employee_name_lower', table_name='employees')
    except Exception:
        pass  # Index may not exist

    # Remove other indexes
    try:
        op.drop_index('uq_employees_crossmark_employee_id', table_name='employees')
    except Exception:
        pass

    try:
        op.drop_index('ix_employees_mv_retail_employee_number', table_name='employees')
    except Exception:
        pass

    # Remove columns using batch mode (required for SQLite DROP COLUMN)
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.drop_column('crossmark_employee_id')
        batch_op.drop_column('mv_retail_employee_number')
