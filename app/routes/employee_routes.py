"""Admin and HR employee-management and directory routes."""

from datetime import date

from flask import Blueprint, request
from sqlalchemy import or_

from app.models import Employee, LeaveRequest
from app.services.employee_service import (
    DuplicateEmployeeError,
    EmployeeValidationError,
    create_employee_account,
)
from app.utils.auth import require_roles
from app.utils.responses import error_response, response, success_response


employee_bp = Blueprint("employees", __name__, url_prefix="/api/employees")


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
    today = date.today()
    approved_leave_ids = {
        employee_id
        for (employee_id,) in (
            LeaveRequest.query.with_entities(LeaveRequest.employee_id)
            .filter(
                LeaveRequest.status == "APPROVED",
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today,
            )
            .all()
        )
    }
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
                "current_status": (
                    "LEAVE"
                    if employee.id in approved_leave_ids
                    else "NOT_CHECKED_IN"
                ),
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
