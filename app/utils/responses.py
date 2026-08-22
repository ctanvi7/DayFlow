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
