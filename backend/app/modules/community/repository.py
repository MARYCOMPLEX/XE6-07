"""社区模块的数据访问。

排序读取 ``CommunityModel`` 上的反范式计数；点赞/收藏在数据库层按用户和模型做唯一约束，
因此这里把已有行视为“已经打开”。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.sql.elements import ColumnElement

from app.models.community import (
    Category,
    Comment,
    CommunityModel,
    Favorite,
    Like,
)
from app.models.enums import ReviewStatus
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category

    async def list_all(self) -> Sequence[Category]:
        stmt = select(Category).order_by(Category.sort_order, Category.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class CommunityModelRepository(BaseRepository[CommunityModel]):
    model = CommunityModel

    _SORT: dict[str, ColumnElement[Any]] = {
        "hot": CommunityModel.hot_score.desc(),
        "new": CommunityModel.created_at.desc(),
        "likes": CommunityModel.like_count.desc(),
    }

    async def browse(
        self,
        *,
        offset: int,
        limit: int,
        category_id: str | None = None,
        sort: str = "hot",
        printable_only: bool = False,
        approved_only: bool = True,
    ) -> Sequence[CommunityModel]:
        stmt = self._base_select()
        if approved_only:
            stmt = stmt.where(CommunityModel.review_status == ReviewStatus.approved)
        if category_id:
            stmt = stmt.where(CommunityModel.category_id == category_id)
        if printable_only:
            stmt = stmt.where(CommunityModel.printable_badge.is_(True))
        stmt = stmt.order_by(self._SORT.get(sort, self._SORT["hot"]))
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def pending_review(self, *, offset: int, limit: int) -> Sequence[CommunityModel]:
        stmt = (
            self._base_select()
            .where(CommunityModel.review_status == ReviewStatus.pending)
            .order_by(CommunityModel.created_at)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class LikeRepository(BaseRepository[Like]):
    model = Like

    async def find(self, user_id: str, model_id: str) -> Like | None:
        return await self.get_by(user_id=user_id, model_id=model_id)


class FavoriteRepository(BaseRepository[Favorite]):
    model = Favorite

    async def find(self, user_id: str, model_id: str) -> Favorite | None:
        return await self.get_by(user_id=user_id, model_id=model_id)


class CommentRepository(BaseRepository[Comment]):
    model = Comment

    async def list_for_model(self, model_id: str, *, offset: int, limit: int) -> Sequence[Comment]:
        return await self.list(model_id=model_id, offset=offset, limit=limit)
