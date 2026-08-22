"""Reusable session-based authentication and authorization helpers."""

from collections.abc import Callable
from functools import wraps

from flask import g, session

from app.extensions import db
from app.models.user import User, UserRole
from app.utils.responses import error_response


def _role_value(role: UserRole | str) -> str:
    return role.value if isinstance(role, UserRole) else str(role).upper()


def get_current_user() -> User | None:
    """Load the active user represented by the current server-side session."""
    user_id = session.get("user_id")
    if user_id is None:
        return None

    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        session.clear()
        return None
    return user


def establish_session(user: User) -> None:
    """Replace any stale session with safe identity data for ``user``."""
    role = _role_value(user.role)
    session.clear()
    session["user_id"] = user.id
    session["role"] = role
    # Retained for compatibility with sibling blueprints that read session.user.
    session["user"] = {"id": user.id, "role": role}


def session_required(view: Callable) -> Callable:
    """Require an active signed-in user, while allowing a password-change flow."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return error_response("Authentication is required.", status_code=401)
        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


def login_required(view: Callable) -> Callable:
    """Require an active user whose initial password has been changed."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return error_response("Authentication is required.", status_code=401)
        if user.must_change_password:
            return error_response(
                "Password change is required before accessing this resource.",
                status_code=403,
            )
        g.current_user = user
        return view(*args, **kwargs)

    return wrapped


def require_roles(*allowed_roles: UserRole | str) -> Callable:
    """Require a signed-in, password-ready user with one of the allowed roles."""
    allowed = {_role_value(role) for role in allowed_roles}

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if user is None:
                return error_response("Authentication is required.", status_code=401)
            if user.must_change_password:
                return error_response(
                    "Password change is required before accessing this resource.",
                    status_code=403,
                )
            if _role_value(user.role) not in allowed:
                return error_response("You do not have permission to perform this action.", status_code=403)
            g.current_user = user
            return view(*args, **kwargs)

        return wrapped

    return decorator


# Keep the original decorator name usable by existing and future modules.
roles_required = require_roles
