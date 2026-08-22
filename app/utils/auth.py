"""Reusable session-based authorization helpers."""

from collections.abc import Callable
from functools import wraps

from flask import session

from app.models.user import UserRole
from app.utils.responses import error_response


def roles_required(*allowed_roles: UserRole) -> Callable:
    """Restrict a route to an authenticated session with an allowed role."""
    allowed = {role.value if isinstance(role, UserRole) else str(role) for role in allowed_roles}

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            current_role = session.get("role")
            if session.get("user_id") is None:
                return error_response("Authentication is required.", status_code=401)
            if current_role not in allowed:
                return error_response("You do not have permission to perform this action.", status_code=403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
