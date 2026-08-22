"""Create idempotent local demo data for the shared Dayflow application.

Run from the repository root with ``python -m scripts.seed_demo``.
"""

import sys
from datetime import date
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

if __package__ in (None, ""):
    print("Run this seed script from the repository root: python -m scripts.seed_demo", file=sys.stderr)
    raise SystemExit(1)

from app import create_app
from app.extensions import db
from app.models import Employee, User, UserRole
from app.services.salary_service import save_salary


class SeedConfigurationError(RuntimeError):
    """Raised when the local demo credentials have not been configured."""


def _ensure_demo_employee(admin: User) -> None:
    """Create the salary branch's demo employee and salary only when absent."""
    employee = admin.employee
    if employee is None:
        employee = Employee(
            user_id=admin.id,
            first_name="Demo",
            last_name="Admin",
            department="People",
            job_title="Administrator",
            date_of_joining=date.today(),
        )
        db.session.add(employee)
        db.session.flush()

    if employee.salary is None:
        save_salary(employee.id, admin.id, "50000")


def seed_demo(app: Any | None = None) -> str:
    """Create configured Admin and compatible salary demo data once."""
    app = app or create_app()
    with app.app_context():
        password = app.config["DEMO_ADMIN_PASSWORD"]
        if not password:
            raise SeedConfigurationError(
                "Set DEMO_ADMIN_PASSWORD in .env before seeding the demo Admin."
            )

        email = app.config["DEMO_ADMIN_EMAIL"].strip().lower()
        login_id = app.config["DEMO_ADMIN_LOGIN_ID"].strip().upper()
        if not email or not login_id:
            raise SeedConfigurationError(
                "Set DEMO_ADMIN_LOGIN_ID and DEMO_ADMIN_EMAIL before seeding the demo Admin."
            )

        admin_by_email = User.query.filter_by(email=email).first()
        admin_by_login_id = User.query.filter_by(login_id=login_id).first()
        created = admin_by_email is None and admin_by_login_id is None

        if created:
            admin = User(
                email=email,
                login_id=login_id,
                role=UserRole.ADMIN,
                must_change_password=False,
                is_active=True,
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.flush()
        else:
            if admin_by_email is not None and admin_by_login_id is not None:
                if admin_by_email.id != admin_by_login_id.id:
                    raise RuntimeError(
                        "The configured demo email and login ID belong to different accounts."
                    )
            admin = admin_by_email or admin_by_login_id
            if admin.role != UserRole.ADMIN.value:
                raise RuntimeError("The configured demo account belongs to a non-Admin account.")

        _ensure_demo_employee(admin)
        db.session.commit()
        return "Demo Admin created." if created else "Demo Admin already exists."


def main() -> int:
    """Run the seed command with CLI-friendly, non-sensitive errors."""
    try:
        print(seed_demo())
    except (SeedConfigurationError, RuntimeError) as exc:
        print(f"Demo Admin was not seeded: {exc}", file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print(
            "Demo Admin was not seeded: database connection or schema is unavailable. "
            "Verify DATABASE_URL and apply migrations.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
