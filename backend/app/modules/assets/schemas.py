"""模型资产及其版本的数据模式。

``AssetRevision`` 表示一次不可变版本，可由生成、上传、修复、切片或导出产生。数据库行只
保存元数据、对象存储 URI 和 hash；二进制产物本身留在存储系统中。响应层应该暴露签名
URL，而不是原始存储 key。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ArtifactType, AssetRevisionStatus, Visibility
from app.schemas.common import TimestampedOut


# -- 创建 / 变更 ----------------------------------------------------------
class ModelAssetCreate(BaseModel):
    project_id: str
    license: str | None = None
    visibility: Visibility = Visibility.private


class RevisionCreate(BaseModel):
    """为资产登记一个新版本。

    ``artifact_type`` 记录版本来源；``parent_revision_id`` 维持版本血缘链，方便工作台
    浏览历史和回滚。
    """

    artifact_type: ArtifactType
    parent_revision_id: str | None = None
    glb_uri: str | None = None
    stl_uri: str | None = None
    extra_uris: dict[str, str] | None = None
    mesh_stats: dict[str, Any] | None = None
    input_hash: str | None = None
    output_hash: str | None = None


# -- 响应 -----------------------------------------------------------------
class RevisionOut(TimestampedOut):
    model_asset_id: str
    parent_revision_id: str | None = None
    schema_version: str = "v0"
    artifact_type: ArtifactType
    status: AssetRevisionStatus
    glb_uri: str | None = None
    stl_uri: str | None = None
    extra_uris: dict[str, str] | None = None
    mesh_stats: dict[str, Any] | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    trace_id: str | None = None


class ModelAssetOut(TimestampedOut):
    project_id: str
    owner_id: str
    current_revision_id: str | None = None
    license: str | None = None
    visibility: Visibility


class ModelAssetDetail(ModelAssetOut):
    revisions: list[RevisionOut] = Field(default_factory=list)


class MeshReportOut(TimestampedOut):
    revision_id: str
    schema_version: str = "v0"
    bbox_mm: dict[str, Any] | None = None
    volume_mm3: float | None = None
    is_watertight: bool | None = None
    is_manifold: bool | None = None
    wall_thickness_mm: float | None = None
    overhang_deg: float | None = None
    printable_score: float | None = None
    issues: list[dict[str, Any]] | None = None
    is_stale: bool = False
