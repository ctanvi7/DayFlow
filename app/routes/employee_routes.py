"""Employee management and caller-safe profile routes."""

from flask import Blueprint, g, request

from app.services.employee_service import (
    EmployeeAccessError,
    EmployeeNotFoundError,
    EmployeeUpdateError,
    DuplicateEmployeeError,
    EmployeeValidationError,
    create_employee_account,
    get_employee_profile_for_user,
    serialize_employee_profile,
    update_employee_profile,
)
from app.utils.auth import login_required, require_roles
from app.utils.responses import error_response, success_response

employee_bp = Blueprint("employees", __name__, url_prefix="/api/employees")


@employee_bp.post("")
@require_roles("ADMIN", "HR")
def create_employee():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Validation failed.", {"body": "A JSON object is required."})

    try:
        employee, temporary_password = create_employee_account(payload)
    except EmployeeValidationError as exc:
        return error_response("Validation failed.", exc.errors)
    except DuplicateEmployeeError as exc:
        return error_response(str(exc), {"email": "Email is already in use."}, status_code=409)
    except RuntimeError:
        return error_response("Unable to create employee. Please try again.", status_code=409)

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
