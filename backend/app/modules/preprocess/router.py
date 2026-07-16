"""模型预处理/后处理 API。

两个接口都是异步入口：校验并入队后返回 ``202`` 和任务句柄。任务进程执行几何处理，写入新的
AssetRevision，并让旧审计/切片失效；因此客户端在切片前必须重新审计新版本。
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUserDep, DbSession
from app.models.enums import JobStatus

from .schemas import PostprocessRequest, PreprocessRequest, ProcessAccepted, ProcessResult
from .service import PreprocessService

router = APIRouter(prefix="/preprocess", tags=["preprocess"])


# -- 预处理：模型进入流水线时规范化 ---------------------------------------
@router.post("/normalize", response_model=ProcessAccepted, status_code=status.HTTP_202_ACCEPTED)
async def normalize(
    body: PreprocessRequest, db: DbSession, user: CurrentUserDep
) -> ProcessAccepted:
    accepted = await PreprocessService(db).preprocess(user.id, body)
    return ProcessAccepted(
        job_ref=accepted.job_ref,
        source_revision_id=accepted.source_revision_id,
        status=JobStatus(accepted.status.value),
    )


# -- 后处理：输出前几何编辑 -----------------------------------------------
@router.post("/postprocess", response_model=ProcessAccepted, status_code=status.HTTP_202_ACCEPTED)
async def postprocess(
    body: PostprocessRequest, db: DbSession, user: CurrentUserDep
) -> ProcessAccepted:
    accepted = await PreprocessService(db).postprocess(user.id, body)
    return ProcessAccepted(
        job_ref=accepted.job_ref,
        source_revision_id=accepted.source_revision_id,
        status=JobStatus(accepted.status.value),
    )


@router.get("/jobs/{job_id}", response_model=ProcessResult)
async def get_process_job(job_id: str, db: DbSession, user: CurrentUserDep) -> ProcessResult:
    """轮询持久化网格处理任务状态及其产出的新版本。"""
    job = await PreprocessService(db).get_job(job_id, user.id)
    return ProcessResult(
        id=job.id,
        created_at=job.created_at,
        updated_at=job.updated_at,
        source_revision_id=job.source_revision_id,
        new_revision_id=job.new_revision_id,
        applied_ops=list(job.operations) if job.status is JobStatus.succeeded else [],
        status=job.status,
        error_message=job.error_message,
    )
