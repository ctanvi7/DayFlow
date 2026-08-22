"""add employee onboarding profile fields

Revision ID: a12c9e5d8f01
Revises: 51e4757a364b
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa


revision = "a12c9e5d8f01"
down_revision = "51e4757a364b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("employees", schema=None) as batch_op:
        batch_op.add_column(sa.Column("date_of_birth", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("gender", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("nationality", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("marital_status", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("manager_name", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("company", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("location", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("pan_no", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("uan_no", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("bank_account_no", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("bank_name", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("ifsc_code", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("profile_image_path", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("employees", schema=None) as batch_op:
        batch_op.drop_column("profile_image_path")
        batch_op.drop_column("ifsc_code")
        batch_op.drop_column("bank_name")
        batch_op.drop_column("bank_account_no")
        batch_op.drop_column("uan_no")
        batch_op.drop_column("pan_no")
        batch_op.drop_column("location")
        batch_op.drop_column("company")
        batch_op.drop_column("manager_name")
        batch_op.drop_column("marital_status")
        batch_op.drop_column("nationality")
        batch_op.drop_column("gender")
        batch_op.drop_column("date_of_birth")
