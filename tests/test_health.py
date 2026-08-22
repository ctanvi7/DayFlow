"""Smoke test for the operational health endpoint."""

from app import create_app


def test_health_endpoint_returns_ok():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )

    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
