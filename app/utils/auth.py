from functools import wraps

from flask import session

from app.utils.responses import response


def require_roles(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = session.get("user")
            if user is None:
                return response(False, message="Authentication required", status=401)
            if user.get("role") not in roles:
                return response(False, message="You are not authorized to perform this action", status=403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
