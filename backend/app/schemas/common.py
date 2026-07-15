"""共享的 Pydantic v2 数据模式基础块。

响应模型和 ORM 模型保持分离，接口不直接返回 ORM 实例。``ORMModel`` 开启
``from_attributes``，让服务层可以直接基于 SQLAlchemy 行对象完成响应校验。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """可从 ORM 行对象读取字段的响应数据模式基类。"""

    model_config = ConfigDict(from_attributes=True)


class TimestampedOut(ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


class Page[T](BaseModel):
    """分页列表响应外壳。"""

    items: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        return (self.total + self.size - 1) // self.size if self.size else 0


class Message(BaseModel):
    """通用确认响应。"""

    message: str = "ok"
