"""可持久追踪网格处理任务的数据访问。"""

from __future__ import annotations

from app.models.workflow import MeshProcessJob
from app.repositories.base import BaseRepository


class MeshProcessJobRepository(BaseRepository[MeshProcessJob]):
    model = MeshProcessJob


__all__ = ["MeshProcessJobRepository"]
