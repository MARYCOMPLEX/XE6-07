"""社区模块数据模式。

覆盖发布/分享、复用/Fork、收藏/点赞/评论、排序、分类浏览和管理员审核。响应模型不允许客户端
伪造内部计数，只从 ``CommunityModel`` 上由服务维护的反范式列读取。
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import ReviewStatus
from app.schemas.common import ORMModel, TimestampedOut


# -- 分类 -----------------------------------------------------------------
class CategoryOut(TimestampedOut):
    name: str
    slug: str
    sort_order: int = 0


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=64)
    sort_order: int = 0


# -- 发布 / 分享 ----------------------------------------------------------
class PublishRequest(BaseModel):
    """把已审计版本发布到社区。"""

    source_revision_id: str
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    license: str | None = None
    cover_uri: str | None = None


class CommunityModelOut(TimestampedOut):
    author_id: str
    source_revision_id: str
    category_id: str | None = None
    title: str
    description: str | None = None
    tags: list[str] | None = None
    license: str | None = None
    cover_uri: str | None = None
    printable_badge: bool = False
    review_status: ReviewStatus
    like_count: int = 0
    favorite_count: int = 0
    comment_count: int = 0
    fork_count: int = 0
    view_count: int = 0
    hot_score: float = 0.0


# -- 派生到工作台 ----------------------------------------------------------
class ForkResult(BaseModel):
    """把社区模型 Fork 到调用者工作台后的结果。"""

    project_id: str
    model_asset_id: str
    revision_id: str


# -- 评论 -----------------------------------------------------------------
class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    parent_id: str | None = None


class CommentOut(TimestampedOut):
    model_id: str
    user_id: str
    parent_id: str | None = None
    content: str


# -- 排序 / 列表过滤 ------------------------------------------------------
class CommunityListFilter(BaseModel):
    category_id: str | None = None
    tag: str | None = None
    sort: str = "hot"  # hot | new | likes
    printable_only: bool = False


# -- 管理员审核 -----------------------------------------------------------
class ReviewDecision(BaseModel):
    status: ReviewStatus
    note: str | None = None


class ToggleResult(ORMModel):
    """点赞或收藏切换后的结果。"""

    active: bool
    count: int
