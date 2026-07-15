"""各流水线模块共享的统一异步任务契约。"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum

from app.contracts import FrozenContract
from app.contracts.artifacts import ArtifactRef


class JobKind(StrEnum):
    generation = "generation"
    printability_check = "printability_check"
    preprocess = "preprocess"
    slicing = "slicing"
    printing = "printing"


class JobState(StrEnum):
    accepted = "accepted"
    pending = "pending"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    timeout = "timeout"


class JobError(FrozenContract):
    code: str
    message: str
    retryable: bool = False
    details: Mapping[str, object] | None = None


class JobHandle(FrozenContract):
    """所有异步命令返回的任务句柄。"""

    job_id: str
    kind: JobKind
    status: JobState
    project_id: str | None = None
    poll_url: str | None = None
    submitted_at: datetime | None = None
    implementation: str | None = None
    simulated: bool = False


class JobResult(FrozenContract):
    """轮询异步任务时返回的传输无关快照。"""

    job_id: str
    kind: JobKind
    status: JobState
    project_id: str | None = None
    artifacts: tuple[ArtifactRef, ...] = ()
    output: Mapping[str, object] | None = None
    error: JobError | None = None
    completed_at: datetime | None = None
    implementation: str | None = None
    simulated: bool = False


__all__ = ["JobError", "JobHandle", "JobKind", "JobResult", "JobState"]
