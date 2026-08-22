"""Leave-request persistence model owned by Member 3.

This module expects the shared Flask-SQLAlchemy instance at
``app.extensions.db`` and the User and Employee models supplied by the shared
foundation.
"""

from __future__ import annotations

from datetime import datetime

from app.extensions import db


class LeaveRequest(db.Model):
    """An employee time-off request and its one-time review decision."""

    __tablename__ = "leave_requests"

    LEAVE_TYPES = ("PAID", "SICK", "UNPAID")
    STATUSES = ("PENDING", "APPROVED", "REJECTED")

    id = db.Column(db.BigInteger, primary_key=True)
    employee_id = db.Column(
        db.BigInteger,
        db.ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )
    leave_type = db.Column(db.String(16), nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    days_requested = db.Column(db.Numeric(5, 1), nullable=False)
    remarks = db.Column(db.String(500), nullable=False)
    attachment_path = db.Column(db.String(255), nullable=True)
    status = db.Column(
        db.String(16), nullable=False, default="PENDING", index=True
    )
    review_comment = db.Column(db.String(500), nullable=True)
    reviewed_by_user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=True,
    )
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # These target classes are supplied by Member 1's shared models.
    employee = db.relationship("Employee", backref="leave_requests")
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_user_id])

    def to_dict(self, include_employee: bool = False) -> dict:
        """Return leave fields safe for UI use."""
        data = {
            "id": self.id,
            "employee_id": self.employee_id,
            "leave_type": self.leave_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "days_requested": float(self.days_requested),
            "remarks": self.remarks,
            "attachment_path": self.attachment_path,
            "status": self.status,
            "review_comment": self.review_comment,
            "reviewed_at": (
                self.reviewed_at.isoformat() if self.reviewed_at else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_employee and self.employee:
            data["employee"] = {
                "id": self.employee.id,
                "first_name": self.employee.first_name,
                "last_name": self.employee.last_name,
                "department": self.employee.department,
                "job_title": self.employee.job_title,
            }
        return data
