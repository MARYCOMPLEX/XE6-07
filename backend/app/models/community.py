"""社区模型：发布、复用/Fork、收藏/点赞/评论、排序、分类与审核。

CommunityModel 是指向源 AssetRevision 的发布快照；Fork 会在用户工作台创建新项目和新版本，
具体复制逻辑在服务层完成。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import ReviewStatus


class Category(UUIDMixin, TimestampMixin, Base):
    """社区分类。"""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CommunityModel(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """用户分享后形成的社区模型。"""

    __tablename__ = "community_models"

    author_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_revision_id: Mapped[str] = mapped_column(
        ForeignKey("asset_revisions.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), default=None, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    tags: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    license: Mapped[str | None] = mapped_column(String(64), default=None)
    cover_uri: Mapped[str | None] = mapped_column(String(512), default=None)
    printable_badge: Mapped[bool] = mapped_column(default=False, nullable=False)
    # 管理员审核。
    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, native_enum=False, length=16),
        default=ReviewStatus.pending,
        nullable=False,
        index=True,
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(32), default=None)
    review_note: Mapped[str | None] = mapped_column(Text, default=None)
    # 排序用反范式计数。
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fork_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hot_score: Mapped[float] = mapped_column(default=0.0, nullable=False, index=True)

    comments: Mapped[list[Comment]] = relationship(
        back_populates="model", cascade="all, delete-orphan"
    )


class Like(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "model_id", name="uq_like_user_model"),)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    model_id: Mapped[str] = mapped_column(
        ForeignKey("community_models.id", ondelete="CASCADE"), index=True, nullable=False
    )


class Favorite(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "model_id", name="uq_fav_user_model"),)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    model_id: Mapped[str] = mapped_column(
        ForeignKey("community_models.id", ondelete="CASCADE"), index=True, nullable=False
    )


class Comment(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "comments"

    model_id: Mapped[str] = mapped_column(
        ForeignKey("community_models.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), default=None
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    model: Mapped[CommunityModel] = relationship(back_populates="comments")
