"""用户与认证接口的骨架测试。

骨架阶段服务层是 mock 桩，这里锁定的是 API 契约与认证/授权依赖的行为，
而非真实持久化逻辑。

注意：本文件不使用 ``from __future__ import annotations``。因为下方有测试在函数内
就地定义路由，延迟注解会让 FastAPI 无法解析局部作用域里的 ``AdminDep`` 依赖，导致
依赖被误当作查询参数（返回 422 而非预期的 401/403）。
"""

from fastapi.testclient import TestClient

from app.core.security import create_access_token, decode_access_token
from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_register_returns_user_without_password() -> None:
    resp = _client().post(
        "/api/v1/users/register",
        json={"email": "a@example.com", "username": "alice", "password": "supersecret"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "alice"
    assert "hashed_password" not in body
    assert "password" not in body


def test_login_issues_bearer_token() -> None:
    resp = _client().post(
        "/api/v1/users/login",
        data={"username": "alice", "password": "supersecret"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert "hashed_password" not in body["user"]


def test_me_requires_authentication() -> None:
    resp = _client().get("/api/v1/users/me")
    assert resp.status_code == 401


def test_me_accepts_valid_bearer_token() -> None:
    token = create_access_token("user-123", extra={"role": "user"})
    resp = _client().get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_access_token_roundtrip_carries_subject_and_role() -> None:
    token = create_access_token("user-123", extra={"role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "admin"


def test_require_admin_dependency_enforces_role() -> None:
    """require_admin 是 #129 管理员身份/对象级授权的基础闸门：非 admin 一律拒绝。"""
    from app.core.deps import AdminDep

    # 用真实应用工厂，确保 AppError（AuthError/PermissionDeniedError）经统一处理器
    # 映射为 401/403，而不是裸 FastAPI 的默认 422。
    app = create_app()

    @app.get("/admin-only")
    async def admin_only(admin: AdminDep) -> dict[str, str]:
        return {"id": admin.id}

    client = TestClient(app)

    user_token = create_access_token("u-1", extra={"role": "user"})
    admin_token = create_access_token("a-1", extra={"role": "admin"})

    assert client.get("/admin-only").status_code == 401
    assert (
        client.get("/admin-only", headers={"Authorization": f"Bearer {user_token}"}).status_code
        == 403
    )
    assert (
        client.get("/admin-only", headers={"Authorization": f"Bearer {admin_token}"}).status_code
        == 200
    )
