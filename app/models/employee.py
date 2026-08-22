"""Employee profile model linked one-to-one with a user account."""

from datetime import datetime

from app.extensions import db
from app.models.user import PRIMARY_KEY_TYPE


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(PRIMARY_KEY_TYPE, primary_key=True)
    user_id = db.Column(PRIMARY_KEY_TYPE, db.ForeignKey("users.id"), unique=True, nullable=False)

    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(50), nullable=True)
    nationality = db.Column(db.String(100), nullable=True)
    marital_status = db.Column(db.String(50), nullable=True)

    department = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    manager_name = db.Column(db.String(160), nullable=True)
    company = db.Column(db.String(160), nullable=True)
    location = db.Column(db.String(160), nullable=True)
    date_of_joining = db.Column(db.Date, nullable=False)

    address = db.Column(db.Text, nullable=True)
    personal_email = db.Column(db.String(255), nullable=True)
    pan_no = db.Column(db.String(32), nullable=True)
    uan_no = db.Column(db.String(32), nullable=True)
    bank_account_no = db.Column(db.String(64), nullable=True)
    bank_name = db.Column(db.String(160), nullable=True)
    ifsc_code = db.Column(db.String(32), nullable=True)
    profile_image_path = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="employee")
    salary = db.relationship("SalaryStructure", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    attendance_records = db.relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Return the standard employee profile without private banking identifiers."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "nationality": self.nationality,
            "marital_status": self.marital_status,
            "department": self.department,
            "job_title": self.job_title,
            "manager_name": self.manager_name,
            "company": self.company,
            "location": self.location,
            "date_of_joining": self.date_of_joining.isoformat() if self.date_of_joining else None,
            "address": self.address,
            "personal_email": self.personal_email,
            "profile_image_path": self.profile_image_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
