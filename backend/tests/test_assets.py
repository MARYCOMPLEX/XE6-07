"""资产与模型版本模块骨架测试。

service 为不落库 mock 桩，这里锁定 API 契约与认证边界：创建/读取资产、登记版本、
查询版本、回滚，以及分页壳与鉴权。响应必须满足 TimestampedOut / 必填字段契约
（回归此前瞬态对象缺 created_at/schema_version 导致 500 的问题）。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token('user-1', extra={'role': 'user'})}"}


# ── 认证边界 ──────────────────────────────────────────────────────────


def test_asset_endpoints_require_auth() -> None:
    c = _client()
    assert c.post("/api/v1/assets", json={"project_id": "p-1"}).status_code == 401
    assert c.get("/api/v1/assets/a-1").status_code == 401


# ── 资产契约 ──────────────────────────────────────────────────────────


def test_create_asset_returns_201_with_timestamps() -> None:
    """创建资产锁定契约：201、visibility 有值、created_at 非空（回归 500）。"""
    resp = _client().post(
        "/api/v1/assets",
        headers=_auth(),
        json={"project_id": "p-1", "visibility": "private"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["visibility"] == "private"
    assert body["created_at"] is not None
    assert body["owner_id"] == "user-1"


def test_create_asset_rejects_unknown_visibility() -> None:
    resp = _client().post(
        "/api/v1/assets",
        headers=_auth(),
        json={"project_id": "p-1", "visibility": "galaxy"},
    )
    assert resp.status_code == 422


def test_get_asset_detail_shape() -> None:
    resp = _client().get("/api/v1/assets/a-1", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert {"project_id", "owner_id", "visibility", "revisions"} <= body.keys()
    assert isinstance(body["revisions"], list)


def test_list_project_assets_is_paginated_shell() -> None:
    resp = _client().get("/api/v1/assets/projects/p-1/assets", headers=_auth())
    assert resp.status_code == 200
    assert {"items", "total", "page", "size"} <= resp.json().keys()


# ── 版本契约 ──────────────────────────────────────────────────────────


def test_add_revision_returns_201_with_required_fields() -> None:
    """登记版本锁定契约：201、schema_version 有值、created_at 非空、字段回显。"""
    resp = _client().post(
        "/api/v1/assets/a-1/revisions",
        headers=_auth(),
        json={"artifact_type": "generated_model", "glb_uri": "mock://m/1.glb"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["schema_version"] == "v0"
    assert body["artifact_type"] == "generated_model"
    assert body["status"] == "created"
    assert body["created_at"] is not None
    assert body["glb_uri"] == "mock://m/1.glb"


def test_add_revision_rejects_unknown_artifact_type() -> None:
    resp = _client().post(
        "/api/v1/assets/a-1/revisions",
        headers=_auth(),
        json={"artifact_type": "teleporter"},
    )
    assert resp.status_code == 422


def test_get_revision_shape() -> None:
    resp = _client().get("/api/v1/assets/revisions/r-1", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == "v0"
    assert body["created_at"] is not None


def test_rollback_returns_message() -> None:
    """回滚只改当前版本指针，回 Message 契约。"""
    resp = _client().post("/api/v1/assets/a-1/rollback/r-1", headers=_auth())
    assert resp.status_code == 200
    assert resp.json()["message"] == "rolled back"
