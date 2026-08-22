"""Authenticated attendance API routes."""

from datetime import datetime

from flask import Blueprint, g, request

from app.services.attendance_service import (
    AttendanceError,
    AttendanceNotFoundError,
    AttendanceService,
    AttendanceValidationError,
)
from app.utils.auth import login_required, require_roles
from app.utils.responses import error_response, success_response


attendance_bp = Blueprint("attendance", __name__)
attendance_service = AttendanceService()


def _current_employee_id() -> int:
    employee = g.current_user.employee
    if employee is None:
        raise AttendanceNotFoundError("Employee profile not found.")
    return employee.id


def _month_filters() -> tuple[int, int]:
    now = datetime.now()
    try:
        year = int(request.args.get("year", now.year))
        month = int(request.args.get("month", now.month))
        datetime(year, month, 1)
    except (TypeError, ValueError) as exc:
        raise AttendanceValidationError("year and month must identify a valid month.") from exc
    return year, month


@attendance_bp.get("/api/attendance/me")
@require_roles("EMPLOYEE")
def my_attendance():
    try:
        employee_id = _current_employee_id()
        year, month = _month_filters()
        records = attendance_service.get_employee_attendance(employee_id, year, month)
        today = attendance_service.get_today_attendance(employee_id)
        current_status = attendance_service.get_current_status(employee_id)
    except AttendanceError as error:
        return error_response(str(error), status_code=error.status_code)

    return success_response(
        {"attendance": [record.to_dict() for record in records], "current_status": current_status},
        "Attendance retrieved successfully.",
    )


@attendance_bp.post("/api/attendance/check-in")
@require_roles("EMPLOYEE")
def check_in():
    try:
        record = attendance_service.check_in(_current_employee_id())
    except AttendanceError as error:
        return error_response(str(error), status_code=error.status_code)
    return success_response(record.to_dict(), "Checked in successfully.", 201)


@attendance_bp.post("/api/attendance/check-out")
@require_roles("EMPLOYEE")
def check_out():
    try:
        record = attendance_service.check_out(_current_employee_id())
    except AttendanceError as error:
        return error_response(str(error), status_code=error.status_code)
    return success_response(record.to_dict(), "Checked out successfully.")


@attendance_bp.get("/api/attendance")
@require_roles("ADMIN", "HR")
def all_attendance():
    try:
        records = attendance_service.get_all_attendance(request.args)
    except AttendanceValidationError as error:
        return error_response(str(error), status_code=error.status_code)
    return success_response([record.to_dict() for record in records], "Attendance retrieved successfully.")


@attendance_bp.get("/api/dashboard/summary")
@login_required
def dashboard_summary():
    if g.current_user.role in {"ADMIN", "HR"}:
        return success_response(
            {"attendance": attendance_service.get_today_summary()},
            "Dashboard summary retrieved successfully.",
        )
    try:
        employee_id = _current_employee_id()
        today = attendance_service.get_today_attendance(employee_id)
        status = attendance_service.get_current_status(employee_id)
    except AttendanceError as error:
        return error_response(str(error), status_code=error.status_code)
    return success_response(
        {
            "attendance": {
                "current_status": status,
                "today": today.to_dict() if today else None,
            }
        },
        "Dashboard summary retrieved successfully.",
    )
