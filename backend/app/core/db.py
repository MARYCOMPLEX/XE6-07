"""数据库会话依赖——骨架模式下为零依赖 mock。

真实实现会在这里创建异步 SQLAlchemy engine 和会话工厂。骨架阶段我们不连接
Postgres：``get_db`` 与 ``session_scope`` 返回一个记录日志的 :class:`MockSession`，
让 ``DbSession`` 依赖和 Celery 任务在没有数据库的情况下也能解析。

ORM 模型（``app.models.*``）作为字段定义保留，只是不再针对真实数据库建表/读写。
接回真实数据库时，用被注释保留的 engine/session 装配替换本文件即可。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from app.core.logging import get_logger

logger = get_logger("db")


class MockSession:
    """记录日志的异步会话替身，接口对齐 AsyncSession 的常用子集。

    骨架里业务逻辑已被 mock 掉，几乎不会真正落库；本替身只保证方法存在且可 await，
    不做任何持久化。
    """

    async def get(self, entity: Any, ident: Any, **_: Any) -> Any:
        logger.debug("db.get", entity=getattr(entity, "__name__", str(entity)), id=ident)
        return None

    async def execute(self, *_: Any, **__: Any) -> MockResult:
        logger.debug("db.execute")
        return MockResult()

    def add(self, obj: Any) -> None:
        logger.debug("db.add", obj=type(obj).__name__)

    async def delete(self, obj: Any) -> None:
        logger.debug("db.delete", obj=type(obj).__name__)

    async def flush(self, *_: Any, **__: Any) -> None:
        logger.debug("db.flush")

    async def commit(self) -> None:
        logger.debug("db.commit")

    async def rollback(self) -> None:
        logger.debug("db.rollback")

    async def close(self) -> None:
        logger.debug("db.close")

    @property
    def sync_session(self) -> Any:
        return self


class MockScalarResult:
    """空查询的标量结果，保持 SQLAlchemy Result 的调用形状。"""

    def all(self) -> list[Any]:
        return []


class MockResult:
    """骨架会话使用的空结果对象。"""

    def scalar_one_or_none(self) -> None:
        return None

    def scalar_one(self) -> int:
        return 0

    def scalars(self) -> MockScalarResult:
        return MockScalarResult()


async def get_db() -> AsyncGenerator[MockSession, None]:
    """FastAPI 依赖：提供一次请求内的会话替身。"""
    session = MockSession()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise


@asynccontextmanager
async def session_scope() -> AsyncGenerator[MockSession, None]:
    """请求周期外使用的会话替身，主要供 Celery 任务进程使用。"""
    session = MockSession()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
