from datetime import date, datetime

import pytest

from app import create_app
from app.extensions import db
from app.models import Attendance, Employee, User, UserRole
from app.services.attendance_service import (
    AttendanceConflictError,
    AttendanceService,
    AttendanceValidationError,
)


PASSWORD = "Password1!"


class Clock:
    def __init__(self, *times):
        self._times = iter(times)

    def __call__(self):
        return next(self._times)


@pytest.fixture()
def app():
    application = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "DEFAULT_BREAK_MINUTES": 60,
        "SCHEDULED_WORK_MINUTES": 480,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


def create_employee(email: str, login_id: str) -> Employee:
    user = User(email=email, login_id=login_id, role=UserRole.EMPLOYEE)
    user.set_password(PASSWORD)
    employee = Employee(
        user=user, first_name="Test", last_name="Employee", department="Engineering",
        job_title="Developer", date_of_joining=date(2026, 8, 1),
    )
    db.session.add(employee)
    db.session.commit()
    return employee


def create_admin() -> User:
    user = User(email="admin@example.local", login_id="ADMIN", role=UserRole.ADMIN)
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, login_id: str):
    response = client.post("/api/auth/login", json={"login_id": login_id, "password": PASSWORD})
    assert response.status_code == 200


def test_successful_check_in_uses_authenticated_employee(app):
    with app.app_context():
        employee = create_employee("employee@example.local", "EMPLOYEE")
        employee_id = employee.id
    client = app.test_client()
    login(client, "EMPLOYEE")
    response = client.post("/api/attendance/check-in", json={"employee_id": 999})
    assert response.status_code == 201
    assert response.get_json()["data"]["employee_id"] == employee_id
    with app.app_context():
        assert Attendance.query.count() == 1


def test_duplicate_check_in_is_rejected(app):
    with app.app_context():
        create_employee("employee@example.local", "EMPLOYEE")
    client = app.test_client()
    login(client, "EMPLOYEE")
    assert client.post("/api/attendance/check-in").status_code == 201
    assert client.post("/api/attendance/check-in").status_code == 409


def test_checkout_without_check_in_is_rejected(app):
    with app.app_context():
        create_employee("employee@example.local", "EMPLOYEE")
    client = app.test_client()
    login(client, "EMPLOYEE")
    assert client.post("/api/attendance/check-out").status_code == 404


def test_successful_checkout_calculates_duration_and_extra_minutes(app):
    with app.app_context():
        employee = create_employee("employee@example.local", "EMPLOYEE")
        service = AttendanceService(clock=Clock(datetime(2026, 8, 22, 9), datetime(2026, 8, 22, 19)))
        service.check_in(employee.id)
        record = service.check_out(employee.id)
        work_minutes = record.work_minutes
        extra_minutes = record.extra_minutes
    assert work_minutes == 540
    assert extra_minutes == 60


def test_work_duration_and_extra_minutes_never_become_negative(app):
    with app.app_context():
        assert AttendanceService.calculate_work_minutes(datetime(2026, 8, 22, 9), datetime(2026, 8, 22, 9, 30), 60) == 0
        assert AttendanceService.calculate_extra_minutes(0) == 0


def test_employee_can_only_read_own_attendance(app):
    with app.app_context():
        employee = create_employee("employee@example.local", "EMPLOYEE")
        other_employee = create_employee("other@example.local", "OTHER")
        employee_id = employee.id
        other_employee_id = other_employee.id
        db.session.add_all([
            Attendance(employee_id=employee.id, attendance_date=date.today(), break_minutes=60),
            Attendance(employee_id=other_employee.id, attendance_date=date.today(), break_minutes=60),
        ])
        db.session.commit()
    client = app.test_client()
    login(client, "EMPLOYEE")
    response = client.get(f"/api/attendance/me?employee_id={other_employee_id}")
    assert response.status_code == 200
    assert [record["employee_id"] for record in response.get_json()["data"]["attendance"]] == [employee_id]


def test_admin_can_access_all_attendance_and_employee_cannot(app):
    with app.app_context():
        employee = create_employee("employee@example.local", "EMPLOYEE")
        create_admin()
        db.session.add(Attendance(employee_id=employee.id, attendance_date=date.today(), break_minutes=60))
        db.session.commit()
    employee_client = app.test_client()
    login(employee_client, "EMPLOYEE")
    assert employee_client.get("/api/attendance").status_code == 403
    admin_client = app.test_client()
    login(admin_client, "ADMIN")
    response = admin_client.get("/api/attendance")
    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 1


def test_invalid_checkout_time_and_double_checkout_are_rejected(app):
    with app.app_context():
        employee = create_employee("employee@example.local", "EMPLOYEE")
        AttendanceService(clock=Clock(datetime(2026, 8, 22, 9))).check_in(employee.id)
        with pytest.raises(AttendanceValidationError):
            AttendanceService(clock=Clock(datetime(2026, 8, 22, 8))).check_out(employee.id)
        AttendanceService(clock=Clock(datetime(2026, 8, 22, 18))).check_out(employee.id)
        with pytest.raises(AttendanceConflictError):
            AttendanceService(clock=Clock(datetime(2026, 8, 22, 19))).check_out(employee.id)


def test_unauthenticated_attendance_requests_are_rejected(app):
    client = app.test_client()
    assert client.get("/api/attendance/me").status_code == 401
    assert client.post("/api/attendance/check-in").status_code == 401
