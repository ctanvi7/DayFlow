"""Role-protected Leave API routes owned by Member 3.

Expected shared imports are documented in LEAVE_IMPLEMENTATION_PLAN.md.
"""

from flask import Blueprint, request, session

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
from app.utils.auth import require_roles
from app.utils.responses import response

leave_bp = Blueprint("leaves", __name__, url_prefix="/api/leaves")


class SessionUserError(LookupError):
    """Raised when an authenticated session lacks a usable user ID."""


def _current_employee_id() -> int:
    user = session.get("user") or {}
    user_id = user.get("id")
    if not isinstance(user_id, int):
        raise SessionUserError("Authenticated session is missing a user ID")
    employee = Employee.query.filter_by(user_id=user_id).first()
    if employee is None:
        raise LookupError("Employee profile not found")
    return employee.id


def _current_user_id() -> int:
    user = session.get("user") or {}
    user_id = user.get("id")
    if not isinstance(user_id, int):
        raise SessionUserError("Authenticated session is missing a user ID")
    return user_id


@leave_bp.get("/me")
@require_roles("EMPLOYEE")
def get_my_leaves():
    try:
        records = list_own_leave_requests(_current_employee_id())
    except LookupError as exc:
        status = 401 if isinstance(exc, SessionUserError) else 404
        return response(False, message=str(exc), status=status)
    return response(True, data=[record.to_dict() for record in records])


@leave_bp.post("")
@require_roles("EMPLOYEE")
def submit_leave():
    try:
        record = create_leave_request(
            _current_employee_id(), request.get_json(silent=True) or {}
        )
    except LookupError as exc:
        status = 401 if isinstance(exc, SessionUserError) else 404
        return response(False, message=str(exc), status=status)
    except LeaveValidationError as exc:
        return response(
            False, message="Validation failed", errors=exc.errors, status=400
        )
    except LeaveConflictError as exc:
        return response(False, message=str(exc), status=409)
    return response(
        True,
        data=record.to_dict(),
        message="Leave request submitted",
        status=201,
    )


@leave_bp.get("")
@require_roles("ADMIN", "HR")
def get_all_leaves():
    try:
        records = list_leave_requests(request.args)
    except LeaveValidationError as exc:
        return response(
            False, message="Validation failed", errors=exc.errors, status=400
        )
    return response(
        True,
        data=[record.to_dict(include_employee=True) for record in records],
    )


@leave_bp.patch("/<int:request_id>/decision")
@require_roles("ADMIN", "HR")
def decide_leave(request_id: int):
    try:
        record = decide_leave_request(
            request_id, _current_user_id(), request.get_json(silent=True) or {}
        )
    except SessionUserError as exc:
        return response(False, message=str(exc), status=401)
    except LeaveNotFoundError as exc:
        return response(False, message=str(exc), status=404)
    except LeaveValidationError as exc:
        return response(
            False, message="Validation failed", errors=exc.errors, status=400
        )
    except LeaveConflictError as exc:
        return response(False, message=str(exc), status=409)
    return response(
        True,
        data=record.to_dict(include_employee=True),
        message="Leave request reviewed",
    )
