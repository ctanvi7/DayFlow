"""Operational health endpoint."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health_check():
    """Return the simple health payload used by the hackathon demo."""
    return jsonify({"status": "ok"})
