"""Consistent JSON response helpers for API blueprints."""

from typing import Any

from flask import jsonify


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
):
    """Build a successful response using the shared API envelope."""
    return jsonify(
        {
            "success": True,
            "data": {} if data is None else data,
            "message": message,
            "errors": None,
        }
    ), status_code


def error_response(
    message: str,
    errors: dict[str, Any] | None = None,
    status_code: int = 400,
):
    """Build a safe client error response without implementation details."""
    return jsonify(
        {
            "success": False,
            "data": None,
            "message": message,
            "errors": {} if errors is None else errors,
        }
    ), status_code


def response(
    success: bool,
    data: Any = None,
    message: str = "Success",
    errors: dict[str, Any] | None = None,
    status: int = 200,
):
    """Compatibility wrapper for blueprints using the older ``response`` API."""
    if success:
        return success_response(data=data, message=message, status_code=status)
    return error_response(message=message, errors=errors, status_code=status)
