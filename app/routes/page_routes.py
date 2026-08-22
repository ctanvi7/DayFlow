"""Server-rendered pages for the leave-management screens."""

from flask import Blueprint, redirect, render_template, session, url_for

from app.models.employee import Employee
from app.utils.auth import page_require_roles


pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def index():
    """Send signed-in users to the page appropriate to their role."""
    user = session.get("user") or {}
    if user.get("role") in {"ADMIN", "HR"}:
        return redirect(url_for("pages.admin_leaves"))
    if user.get("role") == "EMPLOYEE":
        return redirect(url_for("pages.employee_leaves"))
    return redirect(url_for("pages.login"))


@pages_bp.get("/login")
def login():
    """Render the browser login form while preserving the existing login API."""
    user = session.get("user") or {}
    if user.get("role") in {"ADMIN", "HR"}:
        return redirect(url_for("pages.admin_employees"))
    if user.get("role") == "EMPLOYEE":
        return redirect(url_for("pages.employee_attendance"))
    return render_template("index.html")


@pages_bp.get("/leaves")
@page_require_roles("EMPLOYEE")
def employee_leaves():
    return render_template("employee_leaves.html")


@pages_bp.get("/attendance")
@page_require_roles("EMPLOYEE")
def employee_attendance():
    return render_template("attendance/dashboard.html")


@pages_bp.get("/admin/leaves")
@page_require_roles("ADMIN", "HR")
def admin_leaves():
    return render_template("admin_leaves.html")


@pages_bp.get("/admin/employees")
@page_require_roles("ADMIN", "HR")
def admin_employees():
    return render_template("admin_employees.html")


@pages_bp.get("/employees/<int:employee_id>")
@page_require_roles("ADMIN", "HR")
def employee_details(employee_id: int):
    employee = Employee.query.get_or_404(employee_id)
    return render_template("employee_details.html", employee=employee)
