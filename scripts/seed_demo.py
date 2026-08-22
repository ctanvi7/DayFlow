import os
from datetime import date

from app import create_app
from app.extensions import db
from app.models import Employee, User
from app.services.salary_service import save_salary

app = create_app()

with app.app_context():
    email = os.getenv("DEMO_ADMIN_EMAIL", "admin@example.local")
    password = os.getenv("DEMO_ADMIN_PASSWORD")
    if not password:
        raise RuntimeError("Set DEMO_ADMIN_PASSWORD before seeding demo credentials")

    admin = User.query.filter_by(email=email).first()
    if admin is None:
        admin = User(email=email, login_id="OIADMIN", role="ADMIN")
        admin.set_password(password)
        db.session.add(admin)
        db.session.flush()
    elif admin.role != "ADMIN":
        raise RuntimeError("The configured demo account already exists with a non-admin role")

    employee = Employee.query.filter_by(user_id=admin.id).first()
    if employee is None:
        employee = Employee(
            user_id=admin.id, first_name="Demo", last_name="Admin", department="People",
            job_title="Administrator", date_of_joining=date.today(),
        )
        db.session.add(employee)
        db.session.flush()
    if employee.salary is None:
        save_salary(employee.id, admin.id, "50000")
    db.session.commit()
    print(f"Demo admin ready: {email}")
