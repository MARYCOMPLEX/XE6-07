"""打印任务的数据访问，覆盖物理执行生命周期。"""

from __future__ import annotations

from collections.abc import Sequence

from app.models.print import PrintJob
from app.repositories.base import BaseRepository


class PrintJobRepository(BaseRepository[PrintJob]):
    model = PrintJob

    async def for_checklist(self, checklist_id: str) -> PrintJob | None:
        """每个清单只允许一个活跃任务，用于拒绝重复提交。"""
        return await self.get_by(checklist_id=checklist_id)

    async def list_for_printer(
        self, printer_id: str, *, offset: int, limit: int
    ) -> Sequence[PrintJob]:
        return await self.list(printer_id=printer_id, offset=offset, limit=limit)
