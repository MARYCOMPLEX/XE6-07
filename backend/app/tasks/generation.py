"""生成任务进程——骨架 mock 桩版。

真实实现里 API 先写入 ``GenerationJob``，任务进程按 ``provider_chain`` 逐个尝试提供方、
落库产物并推进工作流状态。骨架阶段业务逻辑被 mock 替换：桩版只记录“任务确实被触发”
的日志，不查库、不调编排器、不入队真实任务。函数名与签名保持不变，Celery 注册形状
与真实实现一致。

接回真实逻辑时，用被移除的编排/持久化实现替换本文件即可，调用方无需改动。
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.tasks.broker import celery_app

logger = get_logger("tasks.generation")


@celery_app.task(name="generation.run_generation_job", max_retries=2)  # type: ignore[untyped-decorator]
def run_generation_job(job_id: str, provider_chain: list[str]) -> None:
    """同步 Celery 入口（mock 桩）：只记录任务被触发。"""
    logger.info(
        "generation.run_generation_job(mock)",
        job_id=job_id,
        provider_chain=provider_chain,
    )
