from datetime import datetime

import pytest
from flask import Flask

import app.routes.attendance_routes as attendance_routes
from app.routes.attendance_routes import attendance_bp
from app.services.attendance_service import (
    AttendanceConflictError,
    AttendanceNotFoundError,
    AttendanceService,
)


class Clock:
    def __init__(self, *times):
        self._times = iter(times)

    def __call__(self):
        return next(self._times)


def test_successful_check_in():
    service = AttendanceService(clock=Clock(datetime(2026, 8, 22, 9, 0)))

    record = service.check_in(1)

    assert record.employee_id == 1
    assert record.status == "PRESENT"
    assert record.break_minutes == 60


def test_duplicate_check_in_is_rejected():
    service = AttendanceService(clock=Clock(datetime(2026, 8, 22, 9, 0), datetime(2026, 8, 22, 9, 5)))
    service.check_in(1)

    with pytest.raises(AttendanceConflictError):
        service.check_in(1)


def test_checkout_without_check_in_is_rejected():
    service = AttendanceService(clock=Clock(datetime(2026, 8, 22, 18, 0)))

    with pytest.raises(AttendanceNotFoundError):
        service.check_out(1)


def test_successful_checkout_calculates_duration_and_extra_minutes():
    service = AttendanceService(clock=Clock(datetime(2026, 8, 22, 9, 0), datetime(2026, 8, 22, 19, 0)))
    service.check_in(1)

    record = service.check_out(1)

    assert record.check_out_at == datetime(2026, 8, 22, 19, 0)
    assert record.work_minutes == 540
    assert record.extra_minutes == 60


def test_work_duration_never_becomes_negative():
    assert AttendanceService.calculate_work_minutes(
        datetime(2026, 8, 22, 9, 0), datetime(2026, 8, 22, 9, 30), 60
    ) == 0


def test_employee_attendance_is_owned_by_employee():
    service = AttendanceService(clock=Clock(datetime(2026, 8, 22, 9, 0), datetime(2026, 8, 22, 9, 5)))
    service.check_in(1)
    service.check_in(2)

    records = service.get_employee_attendance(1, 2026, 8)

    assert [record.employee_id for record in records] == [1]


def test_admin_demo_endpoint_returns_all_attendance(monkeypatch):
    service = AttendanceService(clock=Clock(datetime(2026, 8, 22, 9, 0)))
    service.check_in(1)
    monkeypatch.setattr(attendance_routes, "attendance_service", service)
    app = Flask(__name__)
    app.register_blueprint(attendance_bp)

    response = app.test_client().get("/api/attendance")

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"][0]["employee_id"] == 1
