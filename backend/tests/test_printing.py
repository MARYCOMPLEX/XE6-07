"""打印桶骨架测试：预处理 / 设备 / 切片 / 打印。

service 为不落库 mock 桩，这里锁定 API 契约与认证边界，并回归"瞬态对象缺
created_at/progress/diameter 等列默认值导致响应校验 500"的问题（延续 #153/#158）。
四模块共用一个客户端与鉴权头。
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


def test_printing_endpoints_require_auth() -> None:
    c = _client()
    assert c.post("/api/v1/preprocess/normalize", json={"revision_id": "r-1"}).status_code == 401
    assert c.get("/api/v1/devices/printers").status_code == 401
    assert c.post("/api/v1/slicing/slice", json={"revision_id": "r"}).status_code == 401
    assert c.get("/api/v1/print-jobs/pj-1").status_code == 401


# ── 预处理 ────────────────────────────────────────────────────────────


def test_normalize_returns_202_accepted() -> None:
    resp = _client().post(
        "/api/v1/preprocess/normalize", headers=_auth(), json={"revision_id": "r-1"}
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["source_revision_id"] == "r-1"
    assert body["status"] == "pending"


def test_postprocess_requires_at_least_one_op() -> None:
    """PostprocessRequest.ops 有 min_length=1，空列表应 422。"""
    resp = _client().post(
        "/api/v1/preprocess/postprocess", headers=_auth(), json={"revision_id": "r-1", "ops": []}
    )
    assert resp.status_code == 422


def test_get_process_job_has_timestamps() -> None:
    resp = _client().get("/api/v1/preprocess/jobs/j-1", headers=_auth())
    assert resp.status_code == 200
    assert resp.json()["created_at"] is not None


# ── 设备 ──────────────────────────────────────────────────────────────


def test_register_printer_returns_201_with_status_and_timestamps() -> None:
    """回归：瞬态 PrinterDevice 需补 status 与时间戳，否则 PrinterOut 校验 500。"""
    resp = _client().post(
        "/api/v1/devices/printers", headers=_auth(), json={"provider": "mock", "model": "X1C"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["provider"] == "mock"
    assert body["status"] is not None
    assert body["created_at"] is not None


def test_update_spool_recomputes_low_flag() -> None:
    """PATCH 后 remaining_gram 低于 warning_level 时 low=True（依赖 diameter/warning 非空）。"""
    resp = _client().patch(
        "/api/v1/devices/spools/s-1", headers=_auth(), json={"remaining_gram": 10}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["remaining_gram"] == 10
    assert body["low"] is True
    assert body["diameter_mm"] is not None


# ── 切片 ──────────────────────────────────────────────────────────────


def test_slice_returns_202_with_job_handle() -> None:
    resp = _client().post(
        "/api/v1/slicing/slice", headers=_auth(), json={"revision_id": "r-1", "printer_id": "p-1"}
    )
    assert resp.status_code == 202
    assert resp.json()["slice_job_id"]


def test_slice_rejects_unknown_engine() -> None:
    resp = _client().post(
        "/api/v1/slicing/slice",
        headers=_auth(),
        json={"revision_id": "r-1", "printer_id": "p-1", "slicer_engine": "teleporter"},
    )
    assert resp.status_code == 422


def test_get_slice_job_has_timestamps() -> None:
    resp = _client().get("/api/v1/slicing/jobs/sj-1", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "succeeded"
    assert body["created_at"] is not None


def test_build_checklist_is_confirmation_gate() -> None:
    """清单构建产出确认门禁载荷（含时间戳，回归 _checklist_out 的守卫）。"""
    resp = _client().post(
        "/api/v1/slicing/checklists",
        headers=_auth(),
        json={"slice_job_id": "sj-1", "printer_id": "p-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["created_at"] is not None


# ── 打印 ──────────────────────────────────────────────────────────────


def test_submit_print_returns_202() -> None:
    resp = _client().post("/api/v1/print-jobs", headers=_auth(), json={"checklist_id": "c-1"})
    assert resp.status_code == 202
    body = resp.json()
    assert body["print_job_id"]
    assert body["status"] == "queued"


def test_get_print_job_has_progress_and_timestamps() -> None:
    """回归：瞬态 PrintJob 需补 progress 与时间戳，否则 PrintJobOut 校验 500。"""
    resp = _client().get("/api/v1/print-jobs/pj-1", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert body["progress"] == 0.0
    assert body["created_at"] is not None


def test_pickup_marks_picked_up() -> None:
    resp = _client().post(
        "/api/v1/print-jobs/pj-1/pickup", headers=_auth(), json={"pickup_code": "ABC123"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "picked_up"
