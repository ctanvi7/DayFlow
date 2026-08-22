"""Role-protected Leave API routes owned by Member 3.

Expected shared imports are documented in LEAVE_IMPLEMENTATION_PLAN.md.
"""

from flask import Blueprint, request

from app.models.employee import Employee
from app.services.leave_service import (
    LeaveConflictError,
    LeaveNotFoundError,
    LeaveValidationError,
    create_leave_request,
    decide_leave_request,
    list_leave_requests,
    list_own_leave_requests,
)
from app.utils.auth import current_user, login_required, roles_required
from app.utils.responses import error_response, success_response

leave_bp = Blueprint("leaves", __name__, url_prefix="/api/leaves")


def _current_employee_id() -> int:
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    if employee is None:
        raise LookupError("Employee profile not found")
    return employee.id


@leave_bp.get("/me")
@login_required
def get_my_leaves():
    try:
        records = list_own_leave_requests(_current_employee_id())
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response([record.to_dict() for record in records])


@leave_bp.post("")
@login_required
def submit_leave():
    try:
        record = create_leave_request(
            _current_employee_id(), request.get_json(silent=True) or {}
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except LeaveValidationError as exc:
        return error_response(
            "Validation failed", errors=exc.errors, status_code=400
        )
    except LeaveConflictError as exc:
        return error_response(str(exc), status_code=409)
    return success_response(
        record.to_dict(), "Leave request submitted", status_code=201
    )


@leave_bp.get("")
@roles_required("ADMIN", "HR")
def get_all_leaves():
    try:
        records = list_leave_requests(request.args)
    except LeaveValidationError as exc:
        return error_response(
            "Validation failed", errors=exc.errors, status_code=400
        )
    return success_response(
        [record.to_dict(include_employee=True) for record in records]
    )


@leave_bp.patch("/<int:request_id>/decision")
@roles_required("ADMIN", "HR")
def decide_leave(request_id: int):
    try:
        record = decide_leave_request(
            request_id, current_user.id, request.get_json(silent=True) or {}
        )
    except LeaveNotFoundError as exc:
        return error_response(str(exc), status_code=404)
    except LeaveValidationError as exc:
        return error_response(
            "Validation failed", errors=exc.errors, status_code=400
        )
    except LeaveConflictError as exc:
        return error_response(str(exc), status_code=409)
    return success_response(
        record.to_dict(include_employee=True), "Leave request reviewed"
    )
