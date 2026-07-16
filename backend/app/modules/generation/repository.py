"""生成任务及其图片输出的数据访问。"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.enums import JobStatus
from app.models.generation import GeneratedImage, GenerationJob
from app.repositories.base import BaseRepository

# 只有未失败、未取消、未超时的旧任务才值得复用。
_REUSABLE_STATUSES = (
    JobStatus.pending,
    JobStatus.queued,
    JobStatus.running,
    JobStatus.succeeded,
)


class GenerationJobRepository(BaseRepository[GenerationJob]):
    model = GenerationJob

    async def get_with_outputs(self, job_id: str) -> GenerationJob | None:
        # 关联关系使用惰性查询；轮询接口一次只读一个任务，这里按需后续查询即可。
        return await self.get(job_id)

    async def find_reusable(self, project_id: str, input_hash: str) -> GenerationJob | None:
        """在项目范围内按幂等键查找可复用任务。

        返回同 input hash 下最新的可用任务，包括进行中或已成功任务，避免重试重复创建。
        失败或取消的任务会被忽略，让调用方可以重新发起一次尝试。
        """
        stmt = (
            select(GenerationJob)
            .where(
                GenerationJob.project_id == project_id,
                GenerationJob.input_hash == input_hash,
                GenerationJob.status.in_(_REUSABLE_STATUSES),
            )
            .order_by(GenerationJob.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_project(
        self, project_id: str, *, offset: int, limit: int
    ) -> Sequence[GenerationJob]:
        return await self.list(project_id=project_id, offset=offset, limit=limit)


class GeneratedImageRepository(BaseRepository[GeneratedImage]):
    model = GeneratedImage

    async def list_for_job(self, job_id: str) -> Sequence[GeneratedImage]:
        return await self.list(job_id=job_id, limit=100)
