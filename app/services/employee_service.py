"""Transactional employee-account creation service."""

from typing import Any

from flask import current_app
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models import Employee, User, UserRole
from app.utils.id_generator import generate_login_id, generate_temporary_password
from app.utils.validators import (
    EMPLOYEE_PROFILE_FIELDS,
    EMPLOYEE_SELF_EDITABLE_FIELDS,
    validate_employee_payload,
    validate_employee_profile_update,
)


class EmployeeValidationError(ValueError):
    """Raised when employee input fails field validation."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("Employee validation failed.")
        self.errors = errors


class DuplicateEmployeeError(ValueError):
    """Raised when an employee email already belongs to an account."""


class EmployeeNotFoundError(LookupError):
    """Raised when a requested employee profile does not exist."""


class EmployeeAccessError(PermissionError):
    """Raised when a user is not allowed to access an employee profile."""


class EmployeeUpdateError(RuntimeError):
    """Raised when a profile update cannot be committed safely."""


def _role_value(user: User) -> str:
    return user.role.value if isinstance(user.role, UserRole) else str(user.role).upper()


def get_employee_profile_for_user(requesting_user: User, employee_id: int) -> Employee:
    """Return an employee only when the requester is allowed to see it."""
    employee = db.session.get(Employee, employee_id)
    if employee is None:
        raise EmployeeNotFoundError("Employee not found.")

    role = _role_value(requesting_user)
    if role in {UserRole.ADMIN.value, UserRole.HR.value}:
        return employee
    if role == UserRole.EMPLOYEE.value:
        own_employee = requesting_user.employee
        if own_employee is not None and own_employee.id == employee.id:
            return employee

    raise EmployeeAccessError("You do not have permission to access this employee profile.")


def update_employee_profile(requesting_user: User, employee: Employee, payload: dict[str, Any]) -> Employee:
    """Validate and persist an authorized profile update."""
    role = _role_value(requesting_user)
    allowed_fields = (
        EMPLOYEE_PROFILE_FIELDS
        if role in {UserRole.ADMIN.value, UserRole.HR.value}
        else EMPLOYEE_SELF_EDITABLE_FIELDS
    )
    data, errors = validate_employee_profile_update(payload, allowed_fields)
    if errors:
        raise EmployeeValidationError(errors)

    for field_name, value in data.items():
        setattr(employee, field_name, value)

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise EmployeeUpdateError("Unable to update the employee profile.") from exc
    return employee


def serialize_employee_profile(employee: Employee, requesting_user: User) -> dict[str, Any]:
    """Serialize a profile without exposing sensitive employee fields to staff."""
    role = _role_value(requesting_user)
    return employee.to_profile_dict(include_sensitive=role in {UserRole.ADMIN.value, UserRole.HR.value})


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
