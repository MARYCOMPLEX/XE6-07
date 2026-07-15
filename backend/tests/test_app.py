from fastapi.testclient import TestClient

from app.core.exceptions import AppError
from app.main import create_app


def test_health_includes_trace_and_timing_headers() -> None:
    client = TestClient(create_app())

    response = client.get("/health", headers={"x-trace-id": "test-trace"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-trace-id"] == "test-trace"
    assert int(response.headers["x-response-time-ms"]) >= 0


def test_app_error_uses_shared_error_shape() -> None:
    app = create_app()

    @app.get("/expected-error")
    async def expected_error() -> None:
        raise AppError("invalid request", code="invalid_request")

    response = TestClient(app).get("/expected-error")

    assert response.status_code == 400
    assert response.json() == {"error": {"code": "invalid_request", "message": "invalid request"}}
    assert response.headers["x-trace-id"]
    assert response.headers["x-response-time-ms"]


def test_unhandled_error_is_correlated_without_leaking_details() -> None:
    app = create_app()

    @app.get("/unexpected-error")
    async def unexpected_error() -> None:
        raise RuntimeError("sensitive detail")

    response = TestClient(app).get("/unexpected-error", headers={"x-trace-id": "failure-trace"})

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error"}
    }
    assert response.headers["x-trace-id"] == "failure-trace"
    assert response.headers["x-response-time-ms"]
