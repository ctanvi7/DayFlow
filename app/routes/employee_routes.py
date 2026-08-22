"""Admin and HR employee-management routes."""

from flask import Blueprint, request

from app.services.employee_service import (
    DuplicateEmployeeError,
    EmployeeValidationError,
    create_employee_account,
)
from app.utils.auth import require_roles
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
