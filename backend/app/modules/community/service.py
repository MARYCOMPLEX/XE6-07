"""社区逻辑——骨架 mock 桩版。"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.asset import AssetRevision, ModelAsset
from app.models.base import gen_uuid
from app.models.community import Category, Comment, CommunityModel
from app.models.enums import (
    ArtifactType,
    AssetRevisionStatus,
    ProjectStatus,
    ReviewStatus,
    SourceType,
)
from app.models.project import Project

from .schemas import CommentCreate, PublishRequest, ReviewDecision, SortKey

logger = get_logger("community")


def _stamps() -> dict[str, datetime]:
    """瞬态桩对象补 created_at/updated_at；真实场景由 DB server_default 生成。"""
    now = datetime.now(UTC)
    return {"created_at": now, "updated_at": now}


def _counts() -> dict[str, Any]:
    """CommunityModel 的非空反范式列（badge/计数/热度）在瞬态对象上不套用列默认值，
    桩里显式补零，否则 CommunityModelOut 校验 500。真实实现由服务维护这些计数。"""
    return {
        "printable_badge": False,
        "like_count": 0,
        "favorite_count": 0,
        "comment_count": 0,
        "fork_count": 0,
        "view_count": 0,
        "hot_score": 0.0,
    }


class CommunityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- 发布 -------------------------------------------------------------
    async def publish(self, author_id: str, data: PublishRequest) -> CommunityModel:
        logger.info("community.publish(mock)", author_id=author_id, title=data.title)
        return CommunityModel(
            id=gen_uuid(),
            author_id=author_id,
            source_revision_id=data.source_revision_id,
            category_id=data.category_id,
            title=data.title,
            description=data.description,
            tags=data.tags,
            license=data.license,
            cover_uri=data.cover_uri,
            review_status=ReviewStatus.pending,
            **_counts(),
            **_stamps(),
        )

    # -- 派生到工作台 ----------------------------------------------------
    async def fork(self, user_id: str, model_id: str) -> tuple[Project, ModelAsset, AssetRevision]:
        logger.info("community.fork(mock)", user_id=user_id, model_id=model_id)
        project = Project(
            id=gen_uuid(),
            owner_id=user_id,
            title="Fork(mock)",
            source_type=SourceType.community,
            status=ProjectStatus.reviewing_model,
        )
        asset = ModelAsset(id=gen_uuid(), project_id=project.id, owner_id=user_id)
        revision = AssetRevision(
            id=gen_uuid(),
            model_asset_id=asset.id,
            artifact_type=ArtifactType.generated_model,
            status=AssetRevisionStatus.audit_pending,
            glb_uri="mock://models/x.glb",
        )
        return project, asset, revision

    # -- 点赞 / 收藏切换 --------------------------------------------------
    async def toggle_like(self, user_id: str, model_id: str) -> tuple[bool, int]:
        logger.info("community.toggle_like(mock)", user_id=user_id, model_id=model_id)
        return True, 1

    async def toggle_favorite(self, user_id: str, model_id: str) -> tuple[bool, int]:
        logger.info("community.toggle_favorite(mock)", user_id=user_id, model_id=model_id)
        return True, 1

    # -- 评论 -------------------------------------------------------------
    async def add_comment(self, user_id: str, model_id: str, data: CommentCreate) -> Comment:
        logger.info("community.add_comment(mock)", user_id=user_id, model_id=model_id)
        return Comment(
            id=gen_uuid(),
            model_id=model_id,
            user_id=user_id,
            content=data.content,
            parent_id=data.parent_id,
            **_stamps(),
        )

    async def list_comments(
        self, model_id: str, *, offset: int, limit: int
    ) -> tuple[Sequence[Comment], int]:
        logger.info("community.list_comments(mock)", model_id=model_id)
        return [], 0

    # -- 浏览 / 排序 ------------------------------------------------------
    async def browse(
        self,
        *,
        offset: int,
        limit: int,
        category_id: str | None,
        tag: str | None,
        keyword: str | None,
        sort: SortKey,
        printable_only: bool,
    ) -> tuple[Sequence[CommunityModel], int]:
        logger.info(
            "community.browse(mock)",
            category_id=category_id,
            tag=tag,
            keyword=keyword,
            sort=sort,
        )
        return [], 0

    async def get_public(self, model_id: str) -> CommunityModel:
        logger.info("community.get_public(mock)", model_id=model_id)
        return CommunityModel(
            id=model_id,
            author_id=gen_uuid(),
            source_revision_id=gen_uuid(),
            title="(mock)",
            review_status=ReviewStatus.approved,
            **_counts(),
            **_stamps(),
        )

    async def list_categories(self) -> Sequence[Category]:
        logger.info("community.list_categories(mock)")
        return []

    # -- 管理员审核 -------------------------------------------------------
    async def review(
        self, admin_id: str, model_id: str, decision: ReviewDecision
    ) -> CommunityModel:
        logger.info(
            "community.review(mock)",
            admin_id=admin_id,
            model_id=model_id,
            status=decision.status.value,
        )
        return CommunityModel(
            id=model_id,
            author_id=gen_uuid(),
            source_revision_id=gen_uuid(),
            title="(mock)",
            review_status=decision.status,
            reviewed_by=admin_id,
            review_note=decision.note,
            **_counts(),
            **_stamps(),
        )

    async def list_pending(
        self, *, offset: int, limit: int
    ) -> tuple[Sequence[CommunityModel], int]:
        logger.info("community.list_pending(mock)")
        return [], 0
