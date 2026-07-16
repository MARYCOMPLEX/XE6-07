"""生成 API。

变更类接口默认异步：创建 ``GenerationJob`` 后返回 ``202 Accepted`` 和可轮询任务句柄；
提供方调用在任务进程中执行。意图识别是唯一同步接口，因为工作台需要快速确认意图后
再启动生成。
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUserDep, DbSession, PaginationDep
from app.models.enums import JobStatus
from app.schemas.common import OffsetPage

from .schemas import (
    GenerationJobOut,
    ImageToImagesRequest,
    ImageToModelRequest,
    IntentRecognizeRequest,
    IntentRecognizeResult,
    JobAccepted,
    TextToImageRequest,
)
from .service import GenerationService

router = APIRouter(prefix="/generation", tags=["generation"])


# -- 意图识别：同步执行，发生在生成前 -------------------------------------
@router.post("/intent/recognize", response_model=IntentRecognizeResult)
async def recognize_intent(
    body: IntentRecognizeRequest, db: DbSession, user: CurrentUserDep
) -> IntentRecognizeResult:
    return await GenerationService(db).recognize_intent(body.project_id, user.id, body)


# -- 文生图 ---------------------------------------------------------------
@router.post("/text-to-image", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def text_to_image(
    body: TextToImageRequest, db: DbSession, user: CurrentUserDep
) -> JobAccepted:
    job = await GenerationService(db).text_to_image(body.project_id, user.id, body)
    return JobAccepted(job_id=job.id, status=JobStatus(job.status.value))


# -- 图生图 ---------------------------------------------------------------
@router.post("/image-to-images", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def image_to_images(
    body: ImageToImagesRequest, db: DbSession, user: CurrentUserDep
) -> JobAccepted:
    job = await GenerationService(db).image_to_images(body.project_id, user.id, body)
    return JobAccepted(job_id=job.id, status=JobStatus(job.status.value))


# -- 图生 3D 模型 ---------------------------------------------------------
@router.post("/image-to-model", response_model=JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def image_to_model(
    body: ImageToModelRequest, db: DbSession, user: CurrentUserDep
) -> JobAccepted:
    job = await GenerationService(db).image_to_model(body.project_id, user.id, body)
    return JobAccepted(job_id=job.id, status=JobStatus(job.status.value))


# -- 轮询任务 -------------------------------------------------------------
@router.get("/jobs/{job_id}", response_model=GenerationJobOut)
async def get_job(job_id: str, db: DbSession, user: CurrentUserDep) -> GenerationJobOut:
    job = await GenerationService(db).get_job(job_id, user.id)
    return GenerationJobOut.model_validate(job)


@router.get("/projects/{project_id}/jobs", response_model=OffsetPage[GenerationJobOut])
async def list_jobs(
    project_id: str, db: DbSession, user: CurrentUserDep, pg: PaginationDep
) -> OffsetPage[GenerationJobOut]:
    items, total = await GenerationService(db).list_jobs(
        project_id, user.id, offset=pg.offset, limit=pg.size
    )
    return OffsetPage[GenerationJobOut](
        items=[GenerationJobOut.model_validate(i) for i in items],
        total=total,
        page=pg.page,
        size=pg.size,
    )
