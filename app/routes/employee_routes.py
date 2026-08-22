"""Admin, HR, and caller-safe employee profile routes."""

from flask import Blueprint, g, request
from sqlalchemy import or_

from app.models import Employee
from app.services.employee_service import (
    DuplicateEmployeeError,
    EmployeeAccessError,
    EmployeeNotFoundError,
    EmployeeUpdateError,
    EmployeeValidationError,
    create_employee_account,
    get_employee_profile_for_user,
    serialize_employee_profile,
    update_employee_profile,
)
from app.services.attendance_service import AttendanceService
from app.utils.auth import login_required, require_roles
from app.utils.responses import error_response, response, success_response


employee_bp = Blueprint("employees", __name__, url_prefix="/api/employees")
attendance_service = AttendanceService()


@employee_bp.get("")
@require_roles("ADMIN", "HR")
def list_employees():
    """Return the safe employee card fields consumed by admin_directory.js."""
    search = request.args.get("search", "").strip()
    query = Employee.query
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Employee.first_name.ilike(pattern),
                Employee.last_name.ilike(pattern),
                Employee.department.ilike(pattern),
                Employee.job_title.ilike(pattern),
            )
        )
    employees = query.order_by(Employee.first_name, Employee.last_name).all()
    return response(
        True,
        data=[
            {
                "id": employee.id,
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "department": employee.department,
                "job_title": employee.job_title,
                "profile_image_path": employee.profile_image_path,
                "current_status": attendance_service.get_current_status(employee.id),
            }
            for employee in employees
        ],
    )


@employee_bp.post("")
@require_roles("ADMIN", "HR")
def create_employee():
    """Create an employee account and return its one-time credentials."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response(
            "Validation failed.", {"body": "A JSON object is required."}
        )

    try:
        employee, temporary_password = create_employee_account(payload)
    except EmployeeValidationError as exc:
        return error_response("Validation failed.", exc.errors)
    except DuplicateEmployeeError as exc:
        return error_response(
            str(exc), {"email": "Email is already in use."}, status_code=409
        )
    except RuntimeError:
        return error_response(
            "Unable to create employee. Please try again.", status_code=409
        )

    return success_response(
        {
            "employee": employee.to_dict(),
            "credentials": {
                "login_id": employee.user.login_id,
                "temporary_password": temporary_password,
            },
        },
        "Employee created successfully",
        status_code=201,
    )


@employee_bp.get("/<int:employee_id>")
@login_required
def get_employee_profile(employee_id: int):
    """Return a profile only when the authenticated caller may view it."""
    try:
        employee = get_employee_profile_for_user(g.current_user, employee_id)
    except EmployeeNotFoundError as exc:
        return error_response(str(exc), status_code=404)
    except EmployeeAccessError as exc:
        return error_response(str(exc), status_code=403)

    return success_response(
        {"employee": serialize_employee_profile(employee, g.current_user)},
        "Employee profile loaded.",
    )


@employee_bp.patch("/<int:employee_id>")
@login_required
def update_employee_profile_route(employee_id: int):
    """Update only caller-authorized employee profile fields."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Validation failed.", {"body": "A JSON object is required."})

    try:
        employee = get_employee_profile_for_user(g.current_user, employee_id)
        employee = update_employee_profile(g.current_user, employee, payload)
    except EmployeeNotFoundError as exc:
        return error_response(str(exc), status_code=404)
    except EmployeeAccessError as exc:
        return error_response(str(exc), status_code=403)
    except EmployeeValidationError as exc:
        return error_response("Validation failed.", exc.errors)
    except EmployeeUpdateError:
        return error_response("Unable to update the employee profile. Please try again.", status_code=409)

    return success_response(
        {"employee": serialize_employee_profile(employee, g.current_user)},
        "Employee profile updated.",
    )
