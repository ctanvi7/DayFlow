"""Directory data used by the admin employee-directory screen."""

from flask import Blueprint, request
from sqlalchemy import or_

from app.models.employee import Employee
from app.utils.auth import require_roles
from app.utils.responses import response


employee_bp = Blueprint("employees", __name__, url_prefix="/api/employees")


@employee_bp.get("")
@require_roles("ADMIN", "HR")
def list_employees():
    """Return the safe employee card fields consumed by admin_directory.js."""
    search = request.args.get("search", "").strip()
    query = Employee.query
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Employee.first_name.ilike(pattern),
                Employee.last_name.ilike(pattern),
                Employee.department.ilike(pattern),
                Employee.job_title.ilike(pattern),
            )
        )
    employees = query.order_by(Employee.first_name, Employee.last_name).all()
    return response(
        True,
        data=[
            {
                "id": employee.id,
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "department": employee.department,
                "job_title": employee.job_title,
                "profile_image_path": None,
                "current_status": "NOT_CHECKED_IN",
            }
            for employee in employees
        ],
    )
