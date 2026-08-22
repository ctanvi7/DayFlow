from datetime import datetime

from app.extensions import db


PRESENT = "PRESENT"
ABSENT = "ABSENT"
HALF_DAY = "HALF_DAY"
LEAVE = "LEAVE"


class Attendance(db.Model):
    __tablename__ = "attendance"
    __table_args__ = (
        db.UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False, index=True)
    attendance_date = db.Column(db.Date, nullable=False, index=True)
    check_in_at = db.Column(db.DateTime, nullable=True)
    check_out_at = db.Column(db.DateTime, nullable=True)
    break_minutes = db.Column(db.Integer, nullable=False, default=0)
    work_minutes = db.Column(db.Integer, nullable=False, default=0)
    extra_minutes = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(16), nullable=False, default=PRESENT, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = db.relationship("Employee", back_populates="attendance_records")

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "employee_id": self.employee_id,
            "attendance_date": self.attendance_date.isoformat(),
            "check_in_at": self.check_in_at.isoformat() if self.check_in_at else None,
            "check_out_at": self.check_out_at.isoformat() if self.check_out_at else None,
            "break_minutes": self.break_minutes,
            "work_minutes": self.work_minutes,
            "extra_minutes": self.extra_minutes,
            "status": self.status,
        }
        return data
