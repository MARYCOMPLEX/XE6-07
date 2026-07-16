"""模型资产、不可变版本和网格审计报告。

ModelAsset 是逻辑模型容器；AssetRevision 是一次不可变版本，可由生成、上传、修复、切片
或导出产生。产物二进制存放在对象存储中，数据库只保存元数据、URI 和 hash。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ArtifactType, AssetRevisionStatus, Visibility


class ModelAsset(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "model_assets"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    current_revision_id: Mapped[str | None] = mapped_column(String(32), default=None)
    license: Mapped[str | None] = mapped_column(String(64), default=None)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, native_enum=False, length=16),
        default=Visibility.private,
        nullable=False,
    )

    revisions: Mapped[list[AssetRevision]] = relationship(
        back_populates="model_asset",
        cascade="all, delete-orphan",
        order_by="AssetRevision.created_at",
    )


class AssetRevision(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "asset_revisions"

    model_asset_id: Mapped[str] = mapped_column(
        ForeignKey("model_assets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    parent_revision_id: Mapped[str | None] = mapped_column(
        ForeignKey("asset_revisions.id", ondelete="SET NULL"), default=None
    )
    schema_version: Mapped[str] = mapped_column(String(16), default="v0", nullable=False)
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, native_enum=False, length=32), nullable=False
    )
    status: Mapped[AssetRevisionStatus] = mapped_column(
        Enum(AssetRevisionStatus, native_enum=False, length=32),
        default=AssetRevisionStatus.created,
        nullable=False,
        index=True,
    )
    glb_uri: Mapped[str | None] = mapped_column(String(512), default=None)
    stl_uri: Mapped[str | None] = mapped_column(String(512), default=None)
    extra_uris: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    mesh_stats: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    # 可追踪性字段。
    input_hash: Mapped[str | None] = mapped_column(String(64), index=True, default=None)
    output_hash: Mapped[str | None] = mapped_column(String(64), default=None)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True, default=None)

    model_asset: Mapped[ModelAsset] = relationship(back_populates="revisions")
    mesh_reports: Mapped[list[MeshReport]] = relationship(
        back_populates="revision", cascade="all, delete-orphan"
    )


class MeshReport(UUIDMixin, TimestampMixin, Base):
    """某个模型版本的可打印性审计结果。"""

    __tablename__ = "mesh_reports"

    revision_id: Mapped[str] = mapped_column(
        ForeignKey("asset_revisions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    schema_version: Mapped[str] = mapped_column(String(16), default="v0", nullable=False)
    # 几何摘要。
    bbox_mm: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    volume_mm3: Mapped[float | None] = mapped_column(Float, default=None)
    is_watertight: Mapped[bool | None] = mapped_column(default=None)
    is_manifold: Mapped[bool | None] = mapped_column(default=None)
    wall_thickness_mm: Mapped[float | None] = mapped_column(Float, default=None)
    overhang_deg: Mapped[float | None] = mapped_column(Float, default=None)
    printable_score: Mapped[float | None] = mapped_column(Float, default=None)
    # 问题列表，形如 {code, severity(pass/warn/block), message, hint}。
    issues: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    # 下游几何变化时标记为过期。
    is_stale: Mapped[bool] = mapped_column(default=False, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True, default=None)

    revision: Mapped[AssetRevision] = relationship(back_populates="mesh_reports")
