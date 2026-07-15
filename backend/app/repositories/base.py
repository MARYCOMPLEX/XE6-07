"""通用异步仓储基类。

这里封装 SQLAlchemy 模型的常见增删改查，让各领域仓储只需要补充聚合相关查询。
仓储永远不主动提交事务；工作单元边界由请求级会话管理，见 ``core.db.get_db``。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import MockSession
from app.models.base import Base


class BaseRepository[ModelT: Base]:
    """绑定单个 ORM 模型的 CRUD 辅助类。

    子类只需设置 ``model``，再按聚合需要增加查询方法。模型支持软删除时，所有读操作
    默认过滤已删除数据。
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession | MockSession) -> None:
        self.session = session

    # -- 内部辅助 ---------------------------------------------------------
    def _base_select(self) -> Select[tuple[ModelT]]:
        stmt = select(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        return stmt

    # -- 创建 -------------------------------------------------------------
    async def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.flush()
        return obj

    # -- 读取 -------------------------------------------------------------
    async def get(self, obj_id: str) -> ModelT | None:
        stmt = self._base_select().where(self.model.id == obj_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by(self, **filters: Any) -> ModelT | None:
        stmt = self._base_select()
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: Any | None = None,
        **filters: Any,
    ) -> Sequence[ModelT]:
        stmt = self._base_select()
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        elif hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    # -- 更新 / 删除 ------------------------------------------------------
    async def update(self, obj: ModelT, **values: Any) -> ModelT:
        for key, value in values.items():
            setattr(obj, key, value)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        """模型支持软删除时打标删除，否则执行物理删除。"""
        if hasattr(obj, "deleted_at"):
            from datetime import UTC, datetime

            obj.deleted_at = datetime.now(UTC)
            await self.session.flush()
        else:
            await self.session.delete(obj)
            await self.session.flush()
