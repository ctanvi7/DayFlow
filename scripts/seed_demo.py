"""Create idempotent local demo data.

Run from the repository root with ``python -m scripts.seed_demo``.
"""

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db
from app.models import Attendance, Employee, LeaveRequest, SalaryStructure, User, UserRole
from app.services.salary_service import calculate_salary, save_salary

DEMO_EMPLOYEES = (
    ("Aarav", "Sharma", "Engineering", "Backend Developer"),
    ("Maya", "Patel", "Engineering", "QA Engineer"),
    ("Isha", "Mehta", "HR", "HR Specialist"),
    ("Rohan", "Nair", "HR", "Recruiter"),
    ("Anaya", "Singh", "Sales", "Account Executive"),
    ("Kabir", "Rao", "Sales", "Sales Representative"),
)


class SeedConfigurationError(RuntimeError):
    """Raised when required local demo credentials are unavailable."""


def get_or_create_user(email, login_id, role, password):
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, login_id=login_id, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
    return user


def get_or_create_employee(user, first_name, last_name, department, job_title, joining_date):
    employee = Employee.query.filter_by(user_id=user.id).first()
    if employee is None:
        employee = Employee(
            user_id=user.id, first_name=first_name, last_name=last_name,
            department=department, job_title=job_title, date_of_joining=joining_date,
            phone="+919876543210", address="Dayflow Demo Office",
        )
        db.session.add(employee)
        db.session.flush()
    return employee


def business_days_ending_on(end_date, count):
    days = []
    current = end_date
    while len(days) < count:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)
    return list(reversed(days))


def _ensure_demo_employee(admin):
    employee = admin.employee
    if employee is None:
        employee = Employee(
            user_id=admin.id, first_name="Demo", last_name="Admin", department="People",
            job_title="Administrator", date_of_joining=date.today(),
        )
        db.session.add(employee)
        db.session.flush()
    if employee.salary is None:
        save_salary(employee.id, admin.id, "50000")


def _seed_extended_demo(admin, hr, employee_password):
    today = date.today()
    employees = []
    for index, (first_name, last_name, department, job_title) in enumerate(DEMO_EMPLOYEES, 1):
        user = get_or_create_user(
            f"employee{index}@dayflow.local", f"OIEMP{index:04d}", UserRole.EMPLOYEE, employee_password
        )
        employees.append(get_or_create_employee(
            user, first_name, last_name, department, job_title, today - timedelta(days=30)
        ))

    for employee in employees[:2]:
        if employee.salary is None:
            db.session.add(SalaryStructure(
                employee_id=employee.id, updated_by_user_id=admin.id, **calculate_salary("50000")
            ))

    for employee in employees:
        for day in business_days_ending_on(today, 5):
            if Attendance.query.filter_by(employee_id=employee.id, attendance_date=day).first():
                continue
            check_in = datetime.combine(day, datetime.min.time()).replace(hour=9)
            db.session.add(Attendance(
                employee_id=employee.id, attendance_date=day, check_in_at=check_in,
                check_out_at=check_in + timedelta(hours=8, minutes=30), break_minutes=60,
                work_minutes=450, extra_minutes=0, status="PRESENT",
            ))

    pending_start = today + timedelta(days=7)
    approved_start = today + timedelta(days=14)
    if not LeaveRequest.query.filter_by(employee_id=employees[0].id, status="PENDING").first():
        db.session.add(LeaveRequest(
            employee_id=employees[0].id, leave_type="SICK", start_date=pending_start,
            end_date=pending_start, days_requested=1, remarks="Demo pending leave request", status="PENDING",
        ))
    if not LeaveRequest.query.filter_by(employee_id=employees[1].id, status="APPROVED").first():
        db.session.add(LeaveRequest(
            employee_id=employees[1].id, leave_type="PAID", start_date=approved_start,
            end_date=approved_start + timedelta(days=1), days_requested=2,
            remarks="Demo approved leave request", status="APPROVED",
            review_comment="Approved for demo", reviewed_by_user_id=hr.id, reviewed_at=datetime.utcnow(),
        ))


def seed_demo(app: Any | None = None) -> str:
    app = app or create_app()
    with app.app_context():
        password = app.config.get("DEMO_ADMIN_PASSWORD")
        if not password:
            raise SeedConfigurationError("Set DEMO_ADMIN_PASSWORD in .env before seeding the demo Admin.")
        email = app.config.get("DEMO_ADMIN_EMAIL", "admin@example.local").strip().lower()
        login_id = app.config.get("DEMO_ADMIN_LOGIN_ID", "OIADMIN").strip().upper()
        if not email or not login_id:
            raise SeedConfigurationError("Set DEMO_ADMIN_LOGIN_ID and DEMO_ADMIN_EMAIL before seeding the demo Admin.")

        admin_by_email = User.query.filter_by(email=email).first()
        admin_by_login_id = User.query.filter_by(login_id=login_id).first()
        if admin_by_email and admin_by_login_id and admin_by_email.id != admin_by_login_id.id:
            raise RuntimeError("The configured demo email and login ID belong to different accounts.")
        created = admin_by_email is None and admin_by_login_id is None
        admin = admin_by_email or admin_by_login_id
        if admin is None:
            admin = User(email=email, login_id=login_id, role=UserRole.ADMIN, is_active=True)
            admin.set_password(password)
            db.session.add(admin)
            db.session.flush()
        elif admin.role != UserRole.ADMIN.value:
            raise RuntimeError("The configured demo account belongs to a non-Admin account.")

        _ensure_demo_employee(admin)
        hr_password = app.config.get("DEMO_HR_PASSWORD") or os.getenv("DEMO_HR_PASSWORD")
        if hr_password:
            hr = get_or_create_user("hr@dayflow.local", "OIHR", UserRole.HR, hr_password)
            _seed_extended_demo(admin, hr, app.config.get("DEMO_EMPLOYEE_PASSWORD", "DayflowEmployee_2026!"))
        db.session.commit()
        return "Demo Admin created." if created else "Demo Admin already exists."


def main():
    try:
        print(seed_demo())
    except (SeedConfigurationError, RuntimeError) as exc:
        print(f"Demo Admin was not seeded: {exc}", file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("Demo Admin was not seeded: verify DATABASE_URL and apply migrations.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
