"""add_missing_parent_event_ref_num

Revision ID: 835aea74f5fd
Revises: 1c249d0dfbb5
Create Date: 2025-11-22 11:07:01.411125

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '835aea74f5fd'
down_revision = '1c249d0dfbb5'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite doesn't support ALTER TABLE ADD COLUMN with foreign keys directly
    # So we need to do it in two steps

    # Step 1: Add the column without the foreign key
    with op.batch_alter_table('events', schema=None, recreate='never') as batch_op:
        batch_op.add_column(sa.Column('parent_event_ref_num', sa.Integer(), nullable=True))

    # Step 2: Add the foreign key constraint (optional - SQLite doesn't enforce unless PRAGMA foreign_keys=ON)
    # Since SQLite doesn't support adding FK constraints after table creation easily,
    # we'll skip the FK constraint creation. The application-level relationship will work fine.


def downgrade():
    # Remove parent_event_ref_num column from events table
    with op.batch_alter_table('events', schema=None, recreate='never') as batch_op:
        batch_op.drop_column('parent_event_ref_num')
