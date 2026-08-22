"""Security and validation tests for employee profile endpoints."""

from datetime import date

import pytest

from app import create_app
from app.extensions import db
from app.models import Employee, User, UserRole


PASSWORD = "ProfilePass1!"


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )
    with application.app_context():
        db.create_all()
        users = {}
        for name, login_id, role in (
            ("admin", "OIADMIN", UserRole.ADMIN),
            ("hr", "OIHR", UserRole.HR),
            ("employee", "OIEMPA", UserRole.EMPLOYEE),
            ("other", "OIEMPB", UserRole.EMPLOYEE),
        ):
            user = User(email=f"{name}@example.local", login_id=login_id, role=role)
            user.set_password(PASSWORD)
            db.session.add(user)
            users[name] = user
        db.session.flush()

        employees = {}
        for name in ("employee", "other"):
            employee = Employee(
                user_id=users[name].id,
                first_name=name.title(),
                last_name="Member",
                department="Engineering",
                job_title="Developer",
                date_of_joining=date(2026, 1, 1),
                pan_no="ABCDE1234F",
                uan_no="100000000001",
                bank_account_no="123456789012",
                bank_name="Example Bank",
                ifsc_code="EXMP0000001",
            )
            db.session.add(employee)
            employees[name] = employee
        db.session.commit()
        application.profile_ids = {name: employee.id for name, employee in employees.items()}

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


def login(client, login_id: str):
    response = client.post("/api/auth/login", json={"login_id": login_id, "password": PASSWORD})
    assert response.status_code == 200


def test_logged_out_user_cannot_read_profile(app):
    client = app.test_client()
    assert client.get(f"/api/employees/{app.profile_ids['employee']}").status_code == 401


def test_employee_directory_is_limited_to_admin_and_hr(app):
    client = app.test_client()
    assert client.get("/api/employees").status_code == 401

    login(client, "OIEMPA")
    assert client.get("/api/employees").status_code == 403


@pytest.mark.parametrize("login_id", ["OIADMIN", "OIHR"])
def test_admin_and_hr_can_search_the_safe_employee_directory(app, login_id):
    client = app.test_client()
    login(client, login_id)

    response = client.get("/api/employees?search=Employee")

    assert response.status_code == 200
    assert response.get_json()["data"] == [
        {
            "id": app.profile_ids["employee"],
            "first_name": "Employee",
            "last_name": "Member",
                "job_title": "Developer",
                "department": "Engineering",
                "profile_image_path": None,
                "current_status": "NOT_CHECKED_IN",
            }
        ]


@pytest.mark.parametrize("login_id", ["OIADMIN", "OIHR"])
def test_admin_and_hr_can_read_any_profile(app, login_id):
    client = app.test_client()
    login(client, login_id)

    response = client.get(f"/api/employees/{app.profile_ids['employee']}")

    assert response.status_code == 200
    assert response.get_json()["data"]["employee"]["first_name"] == "Employee"


def test_employee_can_read_only_own_safe_profile(app):
    client = app.test_client()
    login(client, "OIEMPA")

    response = client.get(f"/api/employees/{app.profile_ids['employee']}")

    assert response.status_code == 200
    profile = response.get_json()["data"]["employee"]
    for sensitive_field in ("pan_no", "uan_no", "bank_account_no", "bank_name", "ifsc_code", "password_hash", "user_id"):
        assert sensitive_field not in profile
    assert client.get(f"/api/employees/{app.profile_ids['other']}").status_code == 403


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("phone", "+91 98765 43210"),
        ("address", "42 Profile Street"),
        ("personal_email", "PERSONAL@EXAMPLE.LOCAL"),
    ],
)
def test_employee_can_update_own_allowed_personal_fields(app, field_name, value):
    client = app.test_client()
    login(client, "OIEMPA")

    response = client.patch(f"/api/employees/{app.profile_ids['employee']}", json={field_name: value})

    assert response.status_code == 200
    expected = value.lower() if field_name == "personal_email" else value
    assert response.get_json()["data"]["employee"][field_name] == expected


@pytest.mark.parametrize("field_name", ["department", "job_title", "role", "must_change_password", "bank_account_no"])
def test_employee_cannot_change_protected_fields(app, field_name):
    client = app.test_client()
    login(client, "OIEMPA")

    response = client.patch(f"/api/employees/{app.profile_ids['employee']}", json={field_name: "tampered"})

    assert response.status_code == 400
    assert field_name in response.get_json()["errors"]


def test_employee_cannot_update_another_profile(app):
    client = app.test_client()
    login(client, "OIEMPA")

    response = client.patch(f"/api/employees/{app.profile_ids['other']}", json={"phone": "+919876543210"})

    assert response.status_code == 403


def test_admin_can_update_permitted_profile_and_view_sensitive_admin_fields(app):
    client = app.test_client()
    login(client, "OIADMIN")

    response = client.patch(
        f"/api/employees/{app.profile_ids['employee']}",
        json={"department": "People", "date_of_birth": "1999-08-22", "pan_no": "XYZAB1234C"},
    )

    assert response.status_code == 200
    profile = response.get_json()["data"]["employee"]
    assert profile["department"] == "People"
    assert profile["date_of_birth"] == "1999-08-22"
    assert profile["pan_no"] == "XYZAB1234C"
    assert "password_hash" not in profile


@pytest.mark.parametrize(
    "payload",
    [
        {"unknown": "value"},
        {"phone": "not a phone"},
        {"personal_email": "invalid"},
        {"date_of_birth": "2999-01-01"},
    ],
)
def test_profile_update_rejects_unknown_and_invalid_values(app, payload):
    client = app.test_client()
    login(client, "OIADMIN")

    response = client.patch(f"/api/employees/{app.profile_ids['employee']}", json=payload)

    assert response.status_code == 400
    assert response.get_json()["errors"]
