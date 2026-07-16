"""社区桶骨架测试：发布 / Fork / 点赞收藏 / 评论 / 浏览 / 审核。

service 为不落库 mock 桩，这里锁定 API 契约、认证/授权边界，并回归"瞬态对象缺
created_at/反范式计数列默认值导致响应校验 500"的问题（延续 #153/#158/#160）。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token('user-1', extra={'role': 'user'})}"}


def _admin() -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token('adm-1', extra={'role': 'admin'})}"}


# ── 浏览 / 分类 ────────────────────────────────────────────────────────


def test_browse_returns_offset_page() -> None:
    resp = _client().get("/api/v1/community", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert {"total", "page", "size"} <= body.keys()


def test_list_categories_ok() -> None:
    resp = _client().get("/api/v1/community/categories", headers=_auth())
    assert resp.status_code == 200
    assert resp.json() == []


def test_browse_requires_auth() -> None:
    assert _client().get("/api/v1/community").status_code == 401


# ── 发布 / 详情 ────────────────────────────────────────────────────────


def test_publish_returns_201_with_counts_and_timestamps() -> None:
    """回归：CommunityModel 瞬态对象需补时间戳与非空反范式计数，否则序列化 500。"""
    resp = _client().post(
        "/api/v1/community/publish",
        headers=_auth(),
        json={"source_revision_id": "rev-1", "title": "My Model"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "My Model"
    assert body["source_revision_id"] == "rev-1"
    assert body["review_status"] == "pending"
    assert body["like_count"] == 0
    assert body["hot_score"] == 0.0
    assert body["created_at"] is not None


def test_get_public_model_echoes_id() -> None:
    resp = _client().get("/api/v1/community/mdl-9", headers=_auth())
    assert resp.status_code == 200
    assert resp.json()["id"] == "mdl-9"


# ── Fork / 互动 ────────────────────────────────────────────────────────


def test_fork_returns_workbench_handles() -> None:
    resp = _client().post("/api/v1/community/mdl-1/fork", headers=_auth())
    assert resp.status_code == 201
    body = resp.json()
    assert {"project_id", "model_asset_id", "revision_id"} <= body.keys()


def test_toggle_like_returns_state() -> None:
    resp = _client().post("/api/v1/community/mdl-1/like", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert body["active"] is True
    assert isinstance(body["count"], int)


def test_add_comment_returns_201_with_timestamps() -> None:
    """回归：Comment 瞬态对象需补时间戳，否则 CommentOut 序列化 500。"""
    resp = _client().post(
        "/api/v1/community/mdl-1/comments",
        headers=_auth(),
        json={"content": "nice model"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["content"] == "nice model"
    assert body["model_id"] == "mdl-1"
    assert body["created_at"] is not None


def test_add_comment_rejects_empty_content() -> None:
    resp = _client().post("/api/v1/community/mdl-1/comments", headers=_auth(), json={"content": ""})
    assert resp.status_code == 422


# ── 管理员审核 ─────────────────────────────────────────────────────────


def test_review_requires_admin() -> None:
    """普通用户不得访问审核接口。"""
    resp = _client().post(
        "/api/v1/community/admin/mdl-1/review", headers=_auth(), json={"status": "approved"}
    )
    assert resp.status_code == 403


def test_review_as_admin_reflects_decision() -> None:
    resp = _client().post(
        "/api/v1/community/admin/mdl-1/review",
        headers=_admin(),
        json={"status": "approved", "note": "looks good"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "mdl-1"
    assert body["review_status"] == "approved"


def test_list_pending_requires_admin() -> None:
    assert _client().get("/api/v1/community/admin/pending", headers=_auth()).status_code == 403
