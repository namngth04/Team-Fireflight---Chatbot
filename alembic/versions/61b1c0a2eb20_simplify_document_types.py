"""Simplify document types to policy/ops.

Revision ID: 61b1c0a2eb20
Revises: fcfc907d1085
Create Date: 2025-11-15 12:34:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "61b1c0a2eb20"
down_revision = "fcfc907d1085"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE documenttype RENAME TO documenttype_old;")
    op.execute("CREATE TYPE documenttype AS ENUM ('policy', 'ops');")
    op.execute(
        """
        ALTER TABLE documents
        ALTER COLUMN document_type DROP DEFAULT,
        ALTER COLUMN document_type TYPE documenttype
        USING (
            CASE document_type::text
                WHEN 'policies' THEN 'policy'
                WHEN 'processes' THEN 'ops'
                WHEN 'guidelines' THEN 'policy'
                WHEN 'company_info' THEN 'policy'
                WHEN 'forms' THEN 'policy'
                WHEN 'training' THEN 'policy'
                WHEN 'announcements' THEN 'policy'
                WHEN 'technical' THEN 'ops'
                WHEN 'support' THEN 'ops'
                ELSE 'policy'
            END::documenttype
        );
        """
    )
    op.execute("DROP TYPE documenttype_old;")


def downgrade() -> None:
    op.execute("CREATE TYPE documenttype_old AS ENUM ("
               "'policies','processes','guidelines','company_info',"
               "'forms','training','announcements','technical','support');")
    op.execute("ALTER TYPE documenttype RENAME TO documenttype_new;")
    op.execute("ALTER TYPE documenttype_old RENAME TO documenttype;")
    op.execute(
        """
        ALTER TABLE documents
        ALTER COLUMN document_type TYPE documenttype
        USING (
            CASE document_type::text
                WHEN 'policy' THEN 'policies'
                WHEN 'ops' THEN 'technical'
                ELSE 'policies'
            END::documenttype
        );
        """
    )
    op.execute("DROP TYPE documenttype_new;")

