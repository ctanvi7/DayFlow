"""Authentication and employee-onboarding API tests."""

from app import create_app
from app.extensions import db
from app.models import User, UserRole


ADMIN_PASSWORD = "AdminPass1!"
NEW_PASSWORD = "UpdatedPass2!"


def create_app_with_database():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )
    with app.app_context():
        db.create_all()
        admin = User(email="admin@example.local", login_id="OIADMIN", role=UserRole.ADMIN)
        admin.set_password(ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
    return app


def employee_payload(email: str = "john.doe@example.local") -> dict:
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": email,
        "department": "Engineering",
        "job_title": "Developer",
        "date_of_joining": "2026-08-22",
    }


def login(client, login_id: str, password: str):
    return client.post("/api/auth/login", json={"login_id": login_id, "password": password})


def test_login_me_and_logout_flow():
    app = create_app_with_database()
    client = app.test_client()

    assert client.get("/api/auth/me").status_code == 401
    assert login(client, "OIADMIN", "incorrect").status_code == 401

    response = login(client, "OIADMIN", ADMIN_PASSWORD)
    assert response.status_code == 200
    assert response.get_json()["data"]["user"]["role"] == "ADMIN"
    assert client.get("/api/auth/me").status_code == 200

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_admin_creates_employee_and_duplicate_is_rejected():
    app = create_app_with_database()
    client = app.test_client()
    login(client, "OIADMIN", ADMIN_PASSWORD)

    response = client.post("/api/employees", json=employee_payload())
    assert response.status_code == 201
    payload = response.get_json()["data"]
    assert payload["credentials"]["login_id"] == "OIJODO20260001"
    assert payload["credentials"]["temporary_password"]

    with app.app_context():
        employee_user = db.session.scalar(db.select(User).where(User.email == "john.doe@example.local"))
        assert employee_user.password_hash != payload["credentials"]["temporary_password"]
        assert employee_user.must_change_password is True

    assert client.post("/api/employees", json=employee_payload()).status_code == 409


def test_temporary_password_restriction_and_change_flow():
    app = create_app_with_database()
    admin_client = app.test_client()
    login(admin_client, "OIADMIN", ADMIN_PASSWORD)
    created = admin_client.post("/api/employees", json=employee_payload()).get_json()["data"]
    temporary_password = created["credentials"]["temporary_password"]
    employee_login_id = created["credentials"]["login_id"]

    employee_client = app.test_client()
    assert login(employee_client, employee_login_id, temporary_password).status_code == 200
    assert employee_client.post("/api/employees", json=employee_payload("other@example.local")).status_code == 403
    assert employee_client.post(
        "/api/auth/change-password",
        json={"current_password": temporary_password, "new_password": "weak"},
    ).status_code == 400
    assert employee_client.post(
        "/api/auth/change-password",
        json={"current_password": "wrong", "new_password": NEW_PASSWORD},
    ).status_code == 400
    assert employee_client.post(
        "/api/auth/change-password",
        json={"current_password": temporary_password, "new_password": NEW_PASSWORD},
    ).status_code == 200
    assert employee_client.get("/api/auth/me").get_json()["data"]["user"]["must_change_password"] is False

    employee_client.post("/api/auth/logout")
    assert login(employee_client, employee_login_id, temporary_password).status_code == 401
    assert login(employee_client, employee_login_id, NEW_PASSWORD).status_code == 200


def test_employee_cannot_create_an_employee_after_password_change():
    app = create_app_with_database()
    with app.app_context():
        employee = User(email="member@example.local", login_id="OIMEMBER", role=UserRole.EMPLOYEE)
        employee.set_password(NEW_PASSWORD)
        db.session.add(employee)
        db.session.commit()

    client = app.test_client()
    login(client, "OIMEMBER", NEW_PASSWORD)
    assert client.post("/api/employees", json=employee_payload()).status_code == 403
