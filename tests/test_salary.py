from datetime import date
from decimal import Decimal

import pytest

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Employee, User
from app.services.salary_service import calculate_salary


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        admin = User(email="admin@test.local", login_id="ADMIN", password_hash="hash", role="ADMIN")
        employee_user = User(email="employee@test.local", login_id="EMPLOYEE", password_hash="hash", role="EMPLOYEE")
        db.session.add_all([admin, employee_user])
        db.session.flush()
        db.session.add(Employee(user_id=employee_user.id, first_name="Jane", last_name="Doe", department="Engineering", job_title="Developer", date_of_joining=date.today()))
        db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()


def login(client, role, user_id):
    with client.session_transaction() as session:
        session["user"] = {"id": user_id, "role": role}


def test_salary_formula_uses_decimal_and_balances():
    values = calculate_salary("50000")
    assert values["basic_amount"] == Decimal("25000.00")
    assert values["hra_amount"] == Decimal("12500.00")
    assert values["fixed_allowance"] >= 0
    assert sum(values[field] for field in ("basic_amount", "hra_amount", "standard_allowance", "performance_bonus", "lta_amount", "fixed_allowance")) == values["monthly_wage"]


def test_employee_cannot_access_salary_api(app):
    client = app.test_client()
    with app.app_context():
        employee = Employee.query.first()
        login(client, "EMPLOYEE", employee.user_id)
        assert client.get(f"/api/salaries/{employee.id}").status_code == 403


def test_admin_can_save_salary_and_health_is_unchanged(app):
    client = app.test_client()
    with app.app_context():
        employee = Employee.query.first()
        admin = User.query.filter_by(role="ADMIN").first()
        login(client, "ADMIN", admin.id)
        result = client.put(f"/api/salaries/{employee.id}", json={"monthly_wage": "50000"})
        assert result.status_code == 200
        assert result.get_json()["data"]["monthly_wage"] == "50000.00"
        assert client.get("/api/health").get_json() == {"status": "ok"}
