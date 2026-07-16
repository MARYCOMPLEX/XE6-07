"""同步 Celery 入口与异步任务体之间的桥——骨架版。

真实实现里 ``enqueue_after_commit`` 会挂到 SQLAlchemy 的 ``after_commit`` 事件，
确保任务只在事务真正提交后入队。骨架模式用 MockSession，没有真实事务，因此这里
直接内联触发 ``task.delay(...)``（eager 模式下即同步执行任务体）。

``run_async`` 保留原语义：无论调用线程是否已有事件循环都能把协程执行到完成。
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.core.logging import get_logger

logger = get_logger("tasks.enqueue")


def enqueue_after_commit(session: Any, task: Any, **kwargs: Any) -> None:
    """骨架模式：直接内联入队（eager 下即同步执行任务体）。

    真实实现会延迟到数据库事务 ``after_commit`` 再入队；这里没有真实事务，
    因此立即触发并记录日志。
    """
    _ = session
    logger.info("task.enqueued", task=getattr(task, "name", str(task)), kwargs=kwargs)
    task.delay(**kwargs)


def run_async[T](coro: Coroutine[Any, Any, T]) -> T:
    """从同步 Celery task 中把异步任务体执行到完成。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()
