"""Browser-page and directory API coverage for leave-management UI wiring."""

from datetime import date
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.user import User


class TestConfig:
    TESTING = True
    SECRET_KEY = "leave-page-test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def users(app):
    with app.app_context():
        admin = User(email="admin@example.test", password_hash="unused", role="ADMIN")
        employee_user = User(email="employee@example.test", password_hash="unused", role="EMPLOYEE")
        db.session.add_all([admin, employee_user])
        db.session.flush()
        employee = Employee(user_id=employee_user.id, first_name="Esha", last_name="Employee", department="Engineering", job_title="Developer", date_of_joining=date(2026, 1, 1))
        db.session.add(employee)
        db.session.commit()
        return {"admin": {"id": admin.id, "role": "ADMIN"}, "employee": {"id": employee_user.id, "role": "EMPLOYEE"}, "employee_id": employee.id}


def set_session(client, user):
    with client.session_transaction() as session:
        session["user"] = user


def test_landing_page_has_sign_in_form(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"data-login-form" in response.data
    assert b"js/login.js" in response.data


def test_employee_leave_page_has_form_and_script(client, users):
    set_session(client, users["employee"])
    response = client.get("/leaves")
    assert response.status_code == 200
    assert b"data-leave-request-form" in response.data
    assert b"js/leave.js" in response.data
    assert b'value="PAID"' in response.data
    assert b'value="SICK"' in response.data
    assert b'value="UNPAID"' in response.data


def test_admin_pages_and_directory_api(client, users):
    set_session(client, users["admin"])
    assert client.get("/admin/leaves").status_code == 200
    directory = client.get("/admin/employees")
    assert directory.status_code == 200
    assert b"data-employee-directory" in directory.data
    response = client.get("/api/employees?search=Esha")
    assert response.status_code == 200
    assert response.get_json()["data"] == [{"id": users["employee_id"], "first_name": "Esha", "last_name": "Employee", "department": "Engineering", "job_title": "Developer", "profile_image_path": None, "current_status": "NOT_CHECKED_IN"}]


def test_leave_pages_are_role_protected(client, users):
    set_session(client, users["employee"])
    assert client.get("/admin/leaves").status_code == 403
    assert client.get("/api/employees").status_code == 403


def test_directory_marks_employee_on_approved_leave_today(app, client, users):
    with app.app_context():
        db.session.add(
            LeaveRequest(
                employee_id=users["employee_id"],
                leave_type="PAID",
                start_date=date.today(),
                end_date=date.today(),
                days_requested=Decimal("1.0"),
                remarks="Medical appointment",
                status="APPROVED",
            )
        )
        db.session.commit()
    set_session(client, users["admin"])
    response = client.get("/api/employees?search=Esha")
    assert response.status_code == 200
    assert response.get_json()["data"][0]["current_status"] == "LEAVE"
