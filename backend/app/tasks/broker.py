"""Celery 应用——骨架模式下强制 eager，不连接 Redis。

真实部署时 API 侧 ``task.delay(...)`` 入队、独立 worker 执行，两边共享以 Redis 为
中间件的 Celery 应用。骨架阶段我们不依赖 Redis：始终开启 eager 模式，``.delay()``
在调用进程内联执行，任务体本身已被 mock 日志替换。

接回真实队列：去掉下面无条件的 eager 配置，恢复按环境判断即可。
"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery("xe6")

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # 骨架模式：任务始终内联执行并直接抛出异常，无需 Redis / 独立 worker。
    task_always_eager=True,
    task_eager_propagates=True,
    # 仅登记本 PR 落地的任务；slicing/preprocess/printing 随各自模块 PR 追加。
    include=[
        "app.tasks.generation",
    ],
)

_ = settings  # 保留导入：真实实现从 settings.redis_url 读取 broker/backend。
