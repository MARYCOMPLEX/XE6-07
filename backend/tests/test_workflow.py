"""工作流模块骨架测试。

服务层为 mock 桩，这里锁定的是 API 契约、认证边界与状态机行为，而非真实持久化。
状态机是纯领域逻辑（不依赖 mock），所以对它的断言即使接入真实实现后依然成立。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.domain.state_machine import state_machine
from app.main import create_app
from app.models.enums import ProjectStatus as S


def _client() -> TestClient:
    return TestClient(create_app())


def _auth(role: str = "user") -> dict[str, str]:
    token = create_access_token("user-1", extra={"role": role})
    return {"Authorization": f"Bearer {token}"}


# ── 状态机（纯领域逻辑）───────────────────────────────────────────────


def test_state_machine_allows_declared_transition() -> None:
    assert state_machine.can(S.draft, S.input_received) is True


def test_state_machine_rejects_undeclared_transition() -> None:
    """跳步流转必须被拒：draft 不能直接到 slicing。"""
    assert state_machine.can(S.draft, S.slicing) is False


def test_state_machine_same_state_is_idempotent() -> None:
    assert state_machine.can(S.printing, S.printing) is True


def test_archived_is_terminal() -> None:
    assert state_machine.allowed_next(S.archived) == set()


def test_global_exits_reachable_from_active_states() -> None:
    """failed/archived 是几乎所有状态的全局出口。"""
    assert state_machine.can(S.printing, S.failed) is True
    assert state_machine.can(S.generating_model, S.failed) is True


def test_user_command_forbids_system_result_states() -> None:
    """用户指令只能提交自己有权决定的目标；系统结果态须经可信事件进入。"""
    # generating_image 是异步结果态，用户不能直接命令进入。
    assert state_machine.can_user_command(S.draft, S.generating_image) is False
    # revising 是用户可决定的目标。
    assert state_machine.can_user_command(S.completed, S.revising) is True


# ── API 契约与认证边界 ────────────────────────────────────────────────


def test_project_endpoints_require_auth() -> None:
    """未携带 token 一律 401，不泄露工作台资源。"""
    c = _client()
    assert c.get("/api/v1/projects").status_code == 401
    assert c.post("/api/v1/projects", json={}).status_code == 401


def test_create_project_returns_draft_status() -> None:
    """创建项目锁定契约：回 201、初始 status 为 draft、owner 一致于 token。"""
    c = _client()
    resp = c.post(
        "/api/v1/projects",
        headers=_auth(),
        json={"title": "小台灯", "source_type": "text"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "小台灯"
    assert body["status"] == "draft"


def test_create_project_rejects_unknown_source_type() -> None:
    resp = _client().post(
        "/api/v1/projects",
        headers=_auth(),
        json={"title": "x", "source_type": "hologram"},
    )
    assert resp.status_code == 422


def test_user_transition_accepts_legitimate_target() -> None:
    """用户指令端点锁定契约：合法目标回 200 并反映目标状态。

    注意：骨架 service 按设计不做状态机校验（见 service docstring）；对“系统结果态
    不可由用户命令进入”的拒绝逻辑由纯状态机测试
    ``test_user_command_forbids_system_result_states`` 覆盖，接入真实实现后在此补
    API 级拒绝断言。
    """
    c = _client()
    resp = c.post(
        "/api/v1/projects/p-1/transition",
        headers=_auth(),
        json={"target": "revising"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "revising"


def test_list_projects_is_paginated_shell() -> None:
    resp = _client().get("/api/v1/projects", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert {"items", "total", "page", "size"} <= body.keys()


def test_generation_text_to_image_accepts_and_returns_202() -> None:
    """文生图入口锁定契约：合法请求回 202 Accepted（异步任务已受理）。"""
    resp = _client().post(
        "/api/v1/generation/text-to-image",
        headers=_auth(),
        json={"project_id": "p-1", "prompt": "一只赛博朋克猫"},
    )
    assert resp.status_code == 202


def test_generation_rejects_empty_prompt() -> None:
    resp = _client().post(
        "/api/v1/generation/text-to-image",
        headers=_auth(),
        json={"project_id": "p-1", "prompt": ""},
    )
    assert resp.status_code == 422


def test_generation_requires_auth() -> None:
    resp = _client().post(
        "/api/v1/generation/text-to-image",
        json={"project_id": "p-1", "prompt": "x"},
    )
    assert resp.status_code == 401
