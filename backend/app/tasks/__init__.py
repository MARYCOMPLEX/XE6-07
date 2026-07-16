"""异步任务层：基于 Redis 的 Celery。

任务发现由 ``app.tasks.broker`` 中显式的 ``include`` 列表负责。这里保持无副作用，
避免包初始化时递归导入所有任务模块。
"""

__all__: list[str] = []
