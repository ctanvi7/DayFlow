"""Session-based authentication routes."""

from flask import Blueprint, g, request, session
from sqlalchemy import or_, select

from app.extensions import db
from app.models import User
from app.utils.auth import establish_session, session_required
from app.utils.responses import error_response, success_response
from app.utils.validators import password_errors

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _safe_identity(user: User) -> dict:
    data = user.to_dict()
    if user.employee is not None:
        data["employee"] = {
            "id": user.employee.id,
            "first_name": user.employee.first_name,
            "last_name": user.employee.last_name,
            "department": user.employee.department,
            "job_title": user.employee.job_title,
        }
    return data


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    password = payload.get("password")
    login_id = payload.get("login_id")
    email = payload.get("email")

    if not isinstance(password, str) or not password:
        return error_response("Validation failed.", {"password": "Password is required."})
    if not isinstance(login_id, str) and not isinstance(email, str):
        return error_response(
            "Validation failed.",
            {"login_id": "Provide a login ID or email address."},
        )

    predicates = []
    if isinstance(login_id, str) and login_id.strip():
        predicates.append(User.login_id == login_id.strip().upper())
    if isinstance(email, str) and email.strip():
        predicates.append(User.email == email.strip().lower())
    if not predicates:
        return error_response(
            "Validation failed.",
            {"login_id": "Provide a login ID or email address."},
        )

    user = db.session.scalar(select(User).where(or_(*predicates)))
    if user is None or not user.is_active or not user.check_password(password):
        return error_response("Invalid login ID/email or password", status_code=401)

    establish_session(user)
    return success_response({"user": _safe_identity(user)}, "Logged in successfully")


@auth_bp.post("/logout")
@session_required
def logout():
    session.clear()
    return success_response(message="Logged out successfully")


@auth_bp.get("/me")
@session_required
def me():
    return success_response({"user": _safe_identity(g.current_user)}, "Current user loaded")


@auth_bp.post("/change-password")
@session_required
def change_password():
    payload = request.get_json(silent=True) or {}
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")

    if not isinstance(current_password, str) or not current_password:
        return error_response("Validation failed.", {"current_password": "Current password is required."})
    if not g.current_user.check_password(current_password):
        return error_response("Current password is incorrect.", status_code=400)

    errors = password_errors(new_password)
    if errors:
        return error_response("Validation failed.", errors)
    if g.current_user.check_password(new_password):
        return error_response(
            "Validation failed.",
            {"new_password": "New password must differ from the current password."},
        )

    g.current_user.set_password(new_password)
    g.current_user.must_change_password = False
    db.session.commit()
    return success_response({"user": _safe_identity(g.current_user)}, "Password changed successfully")
