"""资产与版本 API：存储关联和版本血缘。

版本不可变；写接口登记新版本，而不是修改旧版本。回滚只改变资产的当前版本指针，
不会删除历史。
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUserDep, DbSession, PaginationDep
from app.schemas.common import Message, OffsetPage

from .schemas import (
    ModelAssetCreate,
    ModelAssetDetail,
    ModelAssetOut,
    RevisionCreate,
    RevisionOut,
)
from .service import AssetService

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=ModelAssetOut, status_code=status.HTTP_201_CREATED)
async def create_asset(
    body: ModelAssetCreate, db: DbSession, user: CurrentUserDep
) -> ModelAssetOut:
    asset = await AssetService(db).create_asset(user.id, body)
    return ModelAssetOut.model_validate(asset)


@router.get("/{asset_id}", response_model=ModelAssetDetail)
async def get_asset(asset_id: str, db: DbSession, user: CurrentUserDep) -> ModelAssetDetail:
    asset = await AssetService(db).get_asset(asset_id, user.id)
    return ModelAssetDetail.model_validate(asset)


@router.get("/projects/{project_id}/assets", response_model=OffsetPage[ModelAssetOut])
async def list_project_assets(
    project_id: str, db: DbSession, user: CurrentUserDep, pg: PaginationDep
) -> OffsetPage[ModelAssetOut]:
    items, total = await AssetService(db).list_for_project(
        project_id, user.id, offset=pg.offset, limit=pg.size
    )
    return OffsetPage[ModelAssetOut](
        items=[ModelAssetOut.model_validate(i) for i in items],
        total=total,
        page=pg.page,
        size=pg.size,
    )


# -- 版本 -----------------------------------------------------------------
@router.post(
    "/{asset_id}/revisions",
    response_model=RevisionOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_revision(
    asset_id: str, body: RevisionCreate, db: DbSession, user: CurrentUserDep
) -> RevisionOut:
    revision = await AssetService(db).add_revision(asset_id, user.id, body)
    return RevisionOut.model_validate(revision)


@router.get("/{asset_id}/revisions", response_model=list[RevisionOut])
async def list_revisions(asset_id: str, db: DbSession, user: CurrentUserDep) -> list[RevisionOut]:
    revisions = await AssetService(db).list_revisions(asset_id, user.id)
    return [RevisionOut.model_validate(r) for r in revisions]


@router.get("/revisions/{revision_id}", response_model=RevisionOut)
async def get_revision(revision_id: str, db: DbSession, user: CurrentUserDep) -> RevisionOut:
    revision = await AssetService(db).get_revision(revision_id, user.id)
    return RevisionOut.model_validate(revision)


@router.post("/{asset_id}/rollback/{revision_id}", response_model=Message)
async def rollback(asset_id: str, revision_id: str, db: DbSession, user: CurrentUserDep) -> Message:
    await AssetService(db).rollback(asset_id, user.id, revision_id)
    return Message(message="rolled back")
