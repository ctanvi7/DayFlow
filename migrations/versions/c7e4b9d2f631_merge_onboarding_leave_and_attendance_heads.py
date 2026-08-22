"""merge onboarding, leave, and attendance migration heads

Revision ID: c7e4b9d2f631
Revises: 806d4f25aa3b, 9a2d70b331cf, a12c9e5d8f01
Create Date: 2026-08-22
"""


revision = "c7e4b9d2f631"
down_revision = ("806d4f25aa3b", "9a2d70b331cf", "a12c9e5d8f01")
branch_labels = None
depends_on = None


def upgrade():
    """Join independent feature migration branches without schema changes."""


def downgrade():
    """Split migration history back into its independent feature branches."""
