"""社区 API。

公开浏览和详情接口需要登录以记录浏览、点赞等归属，但不需要特殊角色。发布、Fork、点赞、
收藏和评论以当前用户身份执行；审核接口要求管理员。Fork 返回新建工作台项目的句柄，方便
客户端直接跳转。
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import AdminDep, CurrentUserDep, DbSession, PaginationDep
from app.schemas.common import OffsetPage

from .schemas import (
    CategoryOut,
    CommentCreate,
    CommentOut,
    CommunityModelOut,
    ForkResult,
    PublishRequest,
    ReviewDecision,
    ToggleResult,
)
from .service import CommunityService

router = APIRouter(prefix="/community", tags=["community"])


# -- 分类 -----------------------------------------------------------------
@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: DbSession, user: CurrentUserDep) -> list[CategoryOut]:
    items = await CommunityService(db).list_categories()
    return [CategoryOut.model_validate(i) for i in items]


# -- 浏览 / 排序 ----------------------------------------------------------
@router.get("", response_model=OffsetPage[CommunityModelOut])
async def browse(
    db: DbSession,
    user: CurrentUserDep,
    pg: PaginationDep,
    category_id: str | None = None,
    sort: str = "hot",
    printable_only: bool = False,
) -> OffsetPage[CommunityModelOut]:
    items, total = await CommunityService(db).browse(
        offset=pg.offset,
        limit=pg.size,
        category_id=category_id,
        sort=sort,
        printable_only=printable_only,
    )
    return OffsetPage[CommunityModelOut](
        items=[CommunityModelOut.model_validate(i) for i in items],
        total=total,
        page=pg.page,
        size=pg.size,
    )


@router.get("/{model_id}", response_model=CommunityModelOut)
async def get_model(model_id: str, db: DbSession, user: CurrentUserDep) -> CommunityModelOut:
    model = await CommunityService(db).get_public(model_id)
    return CommunityModelOut.model_validate(model)


# -- 发布 -----------------------------------------------------------------
@router.post("/publish", response_model=CommunityModelOut, status_code=status.HTTP_201_CREATED)
async def publish(body: PublishRequest, db: DbSession, user: CurrentUserDep) -> CommunityModelOut:
    model = await CommunityService(db).publish(user.id, body)
    return CommunityModelOut.model_validate(model)


# -- 派生到工作台 ----------------------------------------------------------
@router.post("/{model_id}/fork", response_model=ForkResult, status_code=status.HTTP_201_CREATED)
async def fork(model_id: str, db: DbSession, user: CurrentUserDep) -> ForkResult:
    project, asset, revision = await CommunityService(db).fork(user.id, model_id)
    return ForkResult(project_id=project.id, model_asset_id=asset.id, revision_id=revision.id)


# -- 点赞 / 收藏 ----------------------------------------------------------
@router.post("/{model_id}/like", response_model=ToggleResult)
async def toggle_like(model_id: str, db: DbSession, user: CurrentUserDep) -> ToggleResult:
    active, count = await CommunityService(db).toggle_like(user.id, model_id)
    return ToggleResult(active=active, count=count)


@router.post("/{model_id}/favorite", response_model=ToggleResult)
async def toggle_favorite(model_id: str, db: DbSession, user: CurrentUserDep) -> ToggleResult:
    active, count = await CommunityService(db).toggle_favorite(user.id, model_id)
    return ToggleResult(active=active, count=count)


# -- 评论 -----------------------------------------------------------------
@router.post("/{model_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(
    model_id: str, body: CommentCreate, db: DbSession, user: CurrentUserDep
) -> CommentOut:
    comment = await CommunityService(db).add_comment(user.id, model_id, body)
    return CommentOut.model_validate(comment)


@router.get("/{model_id}/comments", response_model=OffsetPage[CommentOut])
async def list_comments(
    model_id: str, db: DbSession, user: CurrentUserDep, pg: PaginationDep
) -> OffsetPage[CommentOut]:
    items, total = await CommunityService(db).list_comments(
        model_id, offset=pg.offset, limit=pg.size
    )
    return OffsetPage[CommentOut](
        items=[CommentOut.model_validate(i) for i in items],
        total=total,
        page=pg.page,
        size=pg.size,
    )


# -- 管理员审核 -----------------------------------------------------------
@router.get("/admin/pending", response_model=OffsetPage[CommunityModelOut])
async def list_pending(
    db: DbSession, admin: AdminDep, pg: PaginationDep
) -> OffsetPage[CommunityModelOut]:
    items, total = await CommunityService(db).list_pending(offset=pg.offset, limit=pg.size)
    return OffsetPage[CommunityModelOut](
        items=[CommunityModelOut.model_validate(i) for i in items],
        total=total,
        page=pg.page,
        size=pg.size,
    )


@router.post("/admin/{model_id}/review", response_model=CommunityModelOut)
async def review(
    model_id: str, body: ReviewDecision, db: DbSession, admin: AdminDep
) -> CommunityModelOut:
    model = await CommunityService(db).review(admin.id, model_id, body)
    return CommunityModelOut.model_validate(model)
