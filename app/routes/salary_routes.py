from flask import Blueprint, request, session

from app.models import Employee
from app.services.salary_service import save_salary
from app.utils.auth import require_roles
from app.utils.responses import response

salary_bp = Blueprint("salary", __name__, url_prefix="/api/salaries")


def serialize_salary(salary):
    return {field: str(getattr(salary, field)) for field in (
        "employee_id", "monthly_wage", "basic_amount", "hra_amount", "standard_allowance",
        "performance_bonus", "lta_amount", "fixed_allowance", "employee_pf", "employer_pf",
        "professional_tax",
    )}


@salary_bp.get("/<int:employee_id>")
@require_roles("ADMIN", "HR")
def get_salary(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    if employee.salary is None:
        return response(True, data=None, message="No salary structure configured")
    return response(True, data=serialize_salary(employee.salary), message="Salary structure loaded")


@salary_bp.put("/<int:employee_id>")
@require_roles("ADMIN", "HR")
def put_salary(employee_id):
    payload = request.get_json(silent=True) or {}
    if "monthly_wage" not in payload:
        return response(False, message="Validation failed", errors={"monthly_wage": "This field is required"}, status=400)
    try:
        salary = save_salary(employee_id, session["user"]["id"], payload["monthly_wage"])
    except ValueError as exc:
        return response(False, message="Validation failed", errors={"monthly_wage": str(exc)}, status=400)
    except LookupError as exc:
        return response(False, message=str(exc), status=404)
    return response(True, data=serialize_salary(salary), message="Salary structure saved")
