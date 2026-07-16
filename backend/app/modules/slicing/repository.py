"""切片任务与打印清单的数据访问。"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.print import PrintChecklist, SliceJob
from app.repositories.base import BaseRepository


class SliceJobRepository(BaseRepository[SliceJob]):
    model = SliceJob

    async def list_for_revision(self, revision_id: str) -> Sequence[SliceJob]:
        return await self.list(revision_id=revision_id, limit=100)

    async def mark_stale_for_revision(self, revision_id: str) -> None:
        """模型版本几何变化时，让相关切片结果失效。"""
        stmt = select(SliceJob).where(SliceJob.revision_id == revision_id)
        result = await self.session.execute(stmt)
        for job in result.scalars().all():
            job.is_stale = True
        await self.session.flush()


class ChecklistRepository(BaseRepository[PrintChecklist]):
    model = PrintChecklist

    async def for_slice_job(self, slice_job_id: str) -> PrintChecklist | None:
        return await self.get_by(slice_job_id=slice_job_id)
