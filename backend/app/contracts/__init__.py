"""跨功能模块共享的稳定契约。

这些契约是不可变的 Pydantic 值对象，刻意不携带 FastAPI、SQLAlchemy、消息队列
或具体提供方类型。这样 HTTP 处理函数、任务进程、测试以及未来新增的传输层，
都可以复用同一组模块边界。
"""

from __future__ import annotations

import datetime as _dt
from collections.abc import Mapping
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class FrozenDict(dict[Any, Any]):
    """保持 JSON 可序列化形状的只读字典。"""

    def _immutable(self, *_: Any, **__: Any) -> None:
        raise TypeError("FrozenDict is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable  # type: ignore[assignment]
    setdefault = _immutable
    update = _immutable
    __ior__ = _immutable  # type: ignore[assignment]


# 这些标量本身不可变，可安全按值保留：JSON 兼容基元 + 常见的不可变值类型。
_FROZEN_SCALARS = (
    str,
    bytes,
    int,
    float,
    bool,
    type(None),
    _dt.datetime,
    _dt.date,
    _dt.time,
    _dt.timedelta,
    Decimal,
    UUID,
    Enum,
)


def _deep_freeze(value: Any) -> Any:
    """把嵌套结构递归冻结成不可变快照。

    只接受不可变标量、标准容器，以及本身已冻结的 ``FrozenContract`` 实例。遇到无法
    冻结的对象（如可变的自定义类实例或普通 Pydantic 模型）时直接抛错，而不是原样
    返回——否则调用方之后改动那个对象，会悄悄改变一个已经构造好的“不可变”契约及其
    序列化输出。
    """
    if isinstance(value, _FROZEN_SCALARS):
        return value
    # 已经是冻结契约（且其嵌套字段在自身构造时已被冻结），按值保留。
    if isinstance(value, FrozenContract):
        return value
    if isinstance(value, Mapping):
        return FrozenDict({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, set | frozenset):
        return frozenset(_deep_freeze(item) for item in value)
    raise TypeError(
        f"契约字段不支持不可冻结的值类型 {type(value).__name__!r}；"
        "请只使用 JSON 兼容的标量、不可变值类型或 FrozenContract。"
    )


class FrozenContract(BaseModel):
    """不可变、字段封闭的跨模块 DTO 基类。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    @model_validator(mode="after")
    def _freeze_nested_values(self) -> FrozenContract:
        for field_name in type(self).model_fields:
            object.__setattr__(self, field_name, _deep_freeze(getattr(self, field_name)))
        return self


# 将少量真正跨模块的契约集中导出，方便发现。
# 这些导入留在底部，因为子模块会继承上面的 ``FrozenContract``。
from app.contracts.artifacts import ArtifactKind, ArtifactRef  # noqa: E402
from app.contracts.jobs import JobError, JobHandle, JobKind, JobResult, JobState  # noqa: E402
from app.contracts.workflow import WorkflowEvent, WorkflowEventKind, WorkflowSource  # noqa: E402

__all__ = [
    "ArtifactKind",
    "ArtifactRef",
    "FrozenContract",
    "JobError",
    "JobHandle",
    "JobKind",
    "JobResult",
    "JobState",
    "WorkflowEvent",
    "WorkflowEventKind",
    "WorkflowSource",
]
