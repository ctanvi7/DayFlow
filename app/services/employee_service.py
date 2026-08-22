"""Transactional employee-account creation service."""

from typing import Any

from flask import current_app
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Employee, User, UserRole
from app.utils.id_generator import generate_login_id, generate_temporary_password
from app.utils.validators import validate_employee_payload


class EmployeeValidationError(ValueError):
    """Raised when employee input fails field validation."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("Employee validation failed.")
        self.errors = errors


class DuplicateEmployeeError(ValueError):
    """Raised when an employee email already belongs to an account."""


def create_employee_account(payload: dict[str, Any]) -> tuple[Employee, str]:
    """Create a User and Employee atomically, returning the one-time password once."""
    employee_data, errors = validate_employee_payload(payload)
    if errors:
        raise EmployeeValidationError(errors)

    for _attempt in range(3):
        temporary_password = generate_temporary_password()
        try:
            existing_user = db.session.scalar(
                select(User.id).where(User.email == employee_data["email"])
            )
            if existing_user is not None:
                raise DuplicateEmployeeError("An account already exists for this email address.")

            login_id = generate_login_id(
                employee_data["first_name"],
                employee_data["last_name"],
                employee_data["date_of_joining"],
            )
            user = User(
                login_id=login_id,
                email=employee_data["email"],
                role=UserRole.EMPLOYEE,
                must_change_password=True,
                is_active=True,
            )
            user.set_password(temporary_password)
            db.session.add(user)
            db.session.flush()

            employee = Employee(
                user_id=user.id,
                first_name=employee_data["first_name"],
                last_name=employee_data["last_name"],
                phone=employee_data.get("phone"),
                department=employee_data["department"],
                job_title=employee_data["job_title"],
                manager_name=employee_data.get("manager_name"),
                company=employee_data.get("company") or current_app.config["COMPANY_NAME"],
                location=employee_data.get("location"),
                date_of_joining=employee_data["date_of_joining"],
            )
            db.session.add(employee)
            db.session.flush()
            db.session.commit()
            return employee, temporary_password
        except DuplicateEmployeeError:
            db.session.rollback()
            raise
        except IntegrityError:
            db.session.rollback()
        except Exception:
            db.session.rollback()
            raise

    raise RuntimeError("Unable to generate a unique employee login ID. Please try again.")
