"""Integration tests for Member 3's Leave API and real application models."""

from datetime import date

import pytest

from app import create_app
from app.extensions import db
from app.models.employee import Employee
from app.models.user import User


class TestConfig:
    TESTING = True
    SECRET_KEY = "leave-test-secret"
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
        employee_user = User(
            email="employee@example.test",
            password_hash="unused",
            role="EMPLOYEE",
        )
        other_employee_user = User(
            email="other@example.test",
            password_hash="unused",
            role="EMPLOYEE",
        )
        admin_user = User(
            email="admin@example.test",
            password_hash="unused",
            role="ADMIN",
        )
        db.session.add_all([employee_user, other_employee_user, admin_user])
        db.session.flush()
        employees = [
            Employee(
                user_id=employee_user.id,
                first_name="Esha",
                last_name="Employee",
                department="Engineering",
                job_title="Developer",
                date_of_joining=date(2026, 1, 1),
            ),
            Employee(
                user_id=other_employee_user.id,
                first_name="Owen",
                last_name="Other",
                department="Design",
                job_title="Designer",
                date_of_joining=date(2026, 1, 1),
            ),
        ]
        db.session.add_all(employees)
        db.session.commit()
        return {
            "employee": {"id": employee_user.id, "role": employee_user.role},
            "employee_id": employees[0].id,
            "other_employee": {
                "id": other_employee_user.id,
                "role": other_employee_user.role,
            },
            "other_employee_id": employees[1].id,
            "admin": {"id": admin_user.id, "role": admin_user.role},
        }


def set_session(client, user):
    with client.session_transaction() as session:
        session["user"] = user


def submit_leave(
    client,
    leave_type="PAID",
    start_date="2026-09-01",
    end_date="2026-09-03",
):
    return client.post(
        "/api/leaves",
        json={
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "remarks": "Family commitment",
        },
    )


@pytest.mark.parametrize("leave_type", ["PAID", "SICK", "UNPAID"])
def test_employee_can_submit_each_allowed_leave_type(
    client, users, leave_type
):
    set_session(client, users["employee"])

    response = submit_leave(client, leave_type=leave_type)

    assert response.status_code == 201
    body = response.get_json()
    assert body["data"]["leave_type"] == leave_type
    assert body["data"]["days_requested"] == 3.0
    assert body["data"]["status"] == "PENDING"


def test_invalid_leave_date_range_is_rejected(client, users):
    set_session(client, users["employee"])

    response = submit_leave(
        client, start_date="2026-09-03", end_date="2026-09-01"
    )

    assert response.status_code == 400
    assert "start_date" in response.get_json()["errors"]


def test_overlapping_pending_leave_is_rejected(client, users):
    set_session(client, users["employee"])
    assert submit_leave(client).status_code == 201

    response = submit_leave(
        client, start_date="2026-09-02", end_date="2026-09-04"
    )

    assert response.status_code == 409


def test_overlapping_approved_leave_is_rejected(client, users):
    set_session(client, users["employee"])
    request_id = submit_leave(client).get_json()["data"]["id"]
    set_session(client, users["admin"])
    assert client.patch(
        f"/api/leaves/{request_id}/decision",
        json={"status": "APPROVED", "review_comment": "Approved"},
    ).status_code == 200
    set_session(client, users["employee"])

    response = submit_leave(
        client, start_date="2026-09-02", end_date="2026-09-04"
    )

    assert response.status_code == 409


def test_overlap_with_rejected_leave_is_allowed(client, users):
    set_session(client, users["employee"])
    request_id = submit_leave(client).get_json()["data"]["id"]
    set_session(client, users["admin"])
    assert client.patch(
        f"/api/leaves/{request_id}/decision",
        json={"status": "REJECTED", "review_comment": "Unavailable"},
    ).status_code == 200
    set_session(client, users["employee"])

    assert submit_leave(
        client, start_date="2026-09-02", end_date="2026-09-04"
    ).status_code == 201


def test_employee_cannot_review_a_leave_request(client, users):
    set_session(client, users["employee"])
    request_id = submit_leave(client).get_json()["data"]["id"]

    response = client.patch(
        f"/api/leaves/{request_id}/decision",
        json={"status": "APPROVED"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize("decision", ["APPROVED", "REJECTED"])
def test_admin_can_review_and_save_comment(client, users, decision):
    set_session(client, users["employee"])
    request_id = submit_leave(client).get_json()["data"]["id"]
    set_session(client, users["admin"])

    response = client.patch(
        f"/api/leaves/{request_id}/decision",
        json={"status": decision, "review_comment": "Manager decision"},
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["status"] == decision
    assert data["review_comment"] == "Manager decision"


def test_employee_can_only_view_own_leave_requests(client, users):
    set_session(client, users["employee"])
    assert submit_leave(client).status_code == 201
    set_session(client, users["other_employee"])
    assert submit_leave(
        client, start_date="2026-10-01", end_date="2026-10-01"
    ).status_code == 201

    response = client.get("/api/leaves/me")

    assert response.status_code == 200
    records = response.get_json()["data"]
    assert len(records) == 1
    assert records[0]["employee_id"] == users["other_employee_id"]
