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


def test_valid_inbound_trace_id_is_preserved() -> None:
    client = TestClient(create_app())

    response = client.get("/health", headers={"x-trace-id": "abc-123-DEF"})

    assert response.headers["x-trace-id"] == "abc-123-DEF"


def test_spoofed_trace_id_is_replaced_with_safe_server_value() -> None:
    client = TestClient(create_app())

    # 含换行/控制字符或超长的伪造值不应被信任、原样回写日志与响应头。
    for bad in ["evil\r\ninjected", "x" * 500, "has space", "bad/slash"]:
        response = client.get("/health", headers={"x-trace-id": bad})
        returned = response.headers["x-trace-id"]
        assert returned != bad
        assert returned.isalnum()  # 服务端生成的 uuid hex
        assert len(returned) == 32


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
