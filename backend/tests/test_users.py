"""用户与认证接口的骨架测试。

骨架阶段服务层是 mock 桩，这里锁定的是 API 契约与认证/授权依赖的行为，
而非真实持久化逻辑。

注意：本文件不使用 ``from __future__ import annotations``。因为下方有测试在函数内
就地定义路由，延迟注解会让 FastAPI 无法解析局部作用域里的 ``AdminDep`` 依赖，导致
依赖被误当作查询参数（返回 422 而非预期的 401/403）。
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
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


def test_password_hash_verify_roundtrip() -> None:
    """锁定 passlib/bcrypt 后端可用：哈希与校验往返正常。

    钉住 bcrypt<5.0 前，passlib 1.7.4 初始化 bcrypt 5.x 会直接抛 ValueError；
    本测试确保锁文件日后不会再引入不兼容组合。
    """
    hashed = hash_password("shortpass")
    assert hashed != "shortpass"
    assert verify_password("shortpass", hashed) is True
    assert verify_password("wrongpass", hashed) is False


def test_create_access_token_rejects_reserved_claim_override() -> None:
    """extra 不能覆盖 sub/exp，避免签发指向非预期身份或有效期的 token。"""
    for reserved in ({"sub": "attacker"}, {"exp": 0}):
        with pytest.raises(ValueError, match="保留声明"):
            create_access_token("real-user", extra=reserved)


def test_login_is_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """生产环境必须拒绝 mock 登录，杜绝任意凭据换取 token 的认证绕过。"""
    from app.core.config import settings

    monkeypatch.setattr(settings, "app_env", "prod")
    resp = _client().post(
        "/api/v1/users/login",
        data={"username": "anyone", "password": "anything"},
    )
    assert resp.status_code == 401


def test_login_token_subject_matches_returned_user_id() -> None:
    """登录响应的 user.id、JWT sub 必须一致，避免客户端登录后身份切换。"""
    resp = _client().post(
        "/api/v1/users/login",
        data={"username": "alice", "password": "supersecret"},
    )
    assert resp.status_code == 200
    body = resp.json()
    claims = decode_access_token(body["access_token"])
    assert claims["sub"] == body["user"]["id"]


def test_bcrypt_does_not_silently_truncate_at_72_bytes() -> None:
    """bcrypt_sha256 消除 bcrypt 72 字节截断：仅第 73 字节不同的口令不得互通。"""
    hashed = hash_password("a" * 72 + "X")
    assert verify_password("a" * 72 + "X", hashed) is True
    assert verify_password("a" * 72 + "Y", hashed) is False


def test_me_preserves_admin_role_from_token() -> None:
    """admin token 请求 /me、PATCH /me 都必须保留 admin，不得降级为 user。"""
    token = create_access_token("admin-1", extra={"role": "admin"})
    h = {"Authorization": f"Bearer {token}"}
    client = _client()
    me = client.get("/api/v1/users/me", headers=h)
    assert me.status_code == 200
    assert me.json()["role"] == "admin"
    patched = client.patch("/api/v1/users/me", headers=h, json={"display_name": "Boss"})
    assert patched.status_code == 200
    assert patched.json()["role"] == "admin"


def test_profile_fields_reject_over_length_values() -> None:
    """输入约束须与 ORM 列长度一致：超长 display_name/avatar_uri 返回 422。"""
    token = create_access_token("user-9", extra={"role": "user"})
    h = {"Authorization": f"Bearer {token}"}
    client = _client()
    assert (
        client.patch("/api/v1/users/me", headers=h, json={"display_name": "x" * 129}).status_code
        == 422
    )
    assert (
        client.patch("/api/v1/users/me", headers=h, json={"avatar_uri": "y" * 513}).status_code
        == 422
    )
    reg = client.post(
        "/api/v1/users/register",
        json={
            "email": "b@e.com",
            "username": "bob",
            "password": "supersecret",
            "display_name": "z" * 129,
        },
    )
    assert reg.status_code == 422


def test_all_mock_routes_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """生产保护须覆盖整个 mock service：register/PATCH 也不得静默成功丢数据。"""
    from app.core.config import settings

    monkeypatch.setattr(settings, "app_env", "prod")
    client = _client()
    reg = client.post(
        "/api/v1/users/register",
        json={"email": "c@e.com", "username": "carol", "password": "supersecret"},
    )
    assert reg.status_code == 401
    token = create_access_token("user-p", extra={"role": "user"})
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/users/me", headers=h).status_code == 401
    assert (
        client.patch("/api/v1/users/me", headers=h, json={"display_name": "x"}).status_code == 401
    )
