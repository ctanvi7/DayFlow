"""Temporary Flask routes for attendance."""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.services.attendance_service import AttendanceError, AttendanceService


attendance_bp = Blueprint("attendance", __name__)
attendance_service = AttendanceService()


def _success(data, message: str, status_code: int = 200):
    return jsonify(success=True, data=data, message=message, errors=None), status_code


def _error(message: str, status_code: int, errors=None):
    return jsonify(success=False, data=None, message=message, errors=errors), status_code


def _employee_id_from_request(default: int | None = None):
    source = request.args if request.method == "GET" else (request.get_json(silent=True) or {})
    value = source.get("employee_id", default)
    try:
        employee_id = int(value)
    except (TypeError, ValueError):
        return None
    return employee_id if employee_id > 0 else None


@attendance_bp.get("/api/attendance/me")
def my_attendance():
    # TODO(Member 2): Replace employee_id request/query parameter with authenticated employee identity after Member 1 auth is merged.
    employee_id = _employee_id_from_request(default=1)
    if employee_id is None:
        return _error("employee_id must be a positive integer.", 400)

    now = datetime.now()
    try:
        year = int(request.args.get("year", now.year))
        month = int(request.args.get("month", now.month))
        if not 1 <= month <= 12:
            raise ValueError
    except ValueError:
        return _error("year and month must be valid integers.", 400)

    records = attendance_service.get_employee_attendance(employee_id, year, month)
    today = attendance_service.get_today_attendance(employee_id)
    current_status = today.status if today else "NOT_CHECKED_IN"
    return _success(
        {"attendance": [record.to_dict() for record in records], "current_status": current_status},
        "Attendance retrieved successfully.",
    )


@attendance_bp.post("/api/attendance/check-in")
def check_in():
    # TODO(Member 2): Replace employee_id request/query parameter with authenticated employee identity after Member 1 auth is merged.
    employee_id = _employee_id_from_request()
    if employee_id is None:
        return _error("employee_id must be a positive integer.", 400)
    try:
        record = attendance_service.check_in(employee_id)
    except AttendanceError as error:
        return _error(str(error), error.status_code)
    return _success(record.to_dict(), "Checked in successfully.", 201)


@attendance_bp.post("/api/attendance/check-out")
def check_out():
    # TODO(Member 2): Replace employee_id request/query parameter with authenticated employee identity after Member 1 auth is merged.
    employee_id = _employee_id_from_request()
    if employee_id is None:
        return _error("employee_id must be a positive integer.", 400)
    try:
        record = attendance_service.check_out(employee_id)
    except AttendanceError as error:
        return _error(str(error), error.status_code)
    return _success(record.to_dict(), "Checked out successfully.")


@attendance_bp.get("/api/attendance")
def all_attendance():
    # TODO(Member 2): Replace temporary admin endpoint with real role authorization after Member 1 auth is merged.
    records = [record.to_dict() for record in attendance_service.get_all_attendance()]
    return _success(records, "Attendance retrieved successfully.")
