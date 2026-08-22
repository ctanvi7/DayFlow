"""create leave requests table

Revision ID: 9a2d70b331cf
Revises: 51e4757a364b
"""

from alembic import op
import sqlalchemy as sa


revision = "9a2d70b331cf"
down_revision = "51e4757a364b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("leave_type", sa.String(length=16), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "days_requested", sa.Numeric(precision=5, scale=1), nullable=False
        ),
        sa.Column("remarks", sa.String(length=500), nullable=False),
        sa.Column("attachment_path", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("review_comment", sa.String(length=500), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_leave_requests_employee_id", "leave_requests", ["employee_id"]
    )
    op.create_index(
        "ix_leave_requests_start_date", "leave_requests", ["start_date"]
    )
    op.create_index(
        "ix_leave_requests_end_date", "leave_requests", ["end_date"]
    )
    op.create_index("ix_leave_requests_status", "leave_requests", ["status"])


def downgrade():
    op.drop_index("ix_leave_requests_status", table_name="leave_requests")
    op.drop_index("ix_leave_requests_end_date", table_name="leave_requests")
    op.drop_index("ix_leave_requests_start_date", table_name="leave_requests")
    op.drop_index("ix_leave_requests_employee_id", table_name="leave_requests")
    op.drop_table("leave_requests")
