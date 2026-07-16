"""资产与版本逻辑（存储关联、版本血缘、失效规则）——骨架 mock 桩版。

真实实现里 ``AssetRevision`` 是不可变版本：创建新版本会连接父版本形成血缘链、推进资产
的 ``current_revision_id``，并按失效规则把父版本审计结果标记为过期；二进制产物放在对象
存储中，本层只记录 URI/hash 并按需发放签名 URL。骨架阶段业务逻辑被 mock 替换：每个方法
只记录“确实被调用”的日志，并返回带 id 的内存桩对象，不查库、不做归属校验、不落库。
方法名、签名与返回类型保持不变，因此上层路由、Agent 工具与脚本看到的业务入口形状与真实
实现一致。

接回真实逻辑时，用被移除的仓储/存储实现替换本文件即可，调用方无需改动。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.storage import StorageClient
from app.models.asset import AssetRevision, ModelAsset
from app.models.base import gen_uuid
from app.models.enums import (
    ArtifactType,
    AssetRevisionStatus,
    ProjectStatus,
    SourceType,
    Visibility,
)
from app.models.project import Project

from .schemas import ModelAssetCreate, RevisionCreate

logger = get_logger("assets")


def _stamps() -> dict[str, datetime]:
    """瞬态桩对象补 created_at/updated_at。

    真实场景由数据库 server_default 生成；骨架不落库，瞬态对象这些字段为 None，
    会导致 TimestampedOut 响应校验失败。接入持久化后本辅助整体移除。
    """
    now = datetime.now(UTC)
    return {"created_at": now, "updated_at": now}


class AssetService:
    def __init__(self, session: AsyncSession, storage: StorageClient | None = None) -> None:
        self.session = session
        self.storage = storage

    # -- 归属校验 ---------------------------------------------------------
    async def get_owned_project(self, project_id: str, owner_id: str) -> Project:
        logger.info("assets.get_owned_project(mock)", project_id=project_id, owner_id=owner_id)
        return Project(
            id=project_id,
            owner_id=owner_id,
            title="(mock)",
            source_type=SourceType.text,
            status=ProjectStatus.draft,
        )

    async def get_owned_asset(self, asset_id: str, owner_id: str) -> ModelAsset:
        logger.info("assets.get_owned_asset(mock)", asset_id=asset_id, owner_id=owner_id)
        return ModelAsset(id=asset_id, project_id=gen_uuid(), owner_id=owner_id)

    # -- 资产 -------------------------------------------------------------
    async def create_asset(self, owner_id: str, data: ModelAssetCreate) -> ModelAsset:
        logger.info("assets.create_asset(mock)", owner_id=owner_id, project_id=data.project_id)
        return ModelAsset(
            id=gen_uuid(),
            project_id=data.project_id,
            owner_id=owner_id,
            license=data.license,
            visibility=data.visibility,
            **_stamps(),
        )

    async def get_asset(self, asset_id: str, owner_id: str) -> ModelAsset:
        logger.info("assets.get_asset(mock)", asset_id=asset_id, owner_id=owner_id)
        # 瞬态对象不套用列默认值；显式补 visibility 与时间戳满足 ModelAssetOut。
        return ModelAsset(
            id=asset_id,
            project_id=gen_uuid(),
            owner_id=owner_id,
            visibility=Visibility.private,
            **_stamps(),
        )

    async def list_for_project(
        self, project_id: str, owner_id: str, *, offset: int, limit: int
    ) -> tuple[Sequence[ModelAsset], int]:
        logger.info("assets.list_for_project(mock)", project_id=project_id, owner_id=owner_id)
        return [], 0

    # -- 版本 -------------------------------------------------------------
    async def add_revision(
        self, asset_id: str, owner_id: str, data: RevisionCreate
    ) -> AssetRevision:
        logger.info("assets.add_revision(mock)", asset_id=asset_id, owner_id=owner_id)
        return AssetRevision(
            id=gen_uuid(),
            model_asset_id=asset_id,
            parent_revision_id=data.parent_revision_id,
            schema_version="v0",
            artifact_type=data.artifact_type,
            status=AssetRevisionStatus.created,
            glb_uri=data.glb_uri,
            stl_uri=data.stl_uri,
            extra_uris=data.extra_uris,
            mesh_stats=data.mesh_stats,
            input_hash=data.input_hash,
            output_hash=data.output_hash,
            **_stamps(),
        )

    async def list_revisions(self, asset_id: str, owner_id: str) -> Sequence[AssetRevision]:
        logger.info("assets.list_revisions(mock)", asset_id=asset_id, owner_id=owner_id)
        return []

    async def get_revision(self, revision_id: str, owner_id: str) -> AssetRevision:
        logger.info("assets.get_revision(mock)", revision_id=revision_id, owner_id=owner_id)
        return AssetRevision(
            id=revision_id,
            model_asset_id=gen_uuid(),
            schema_version="v0",
            artifact_type=ArtifactType.generated_model,
            status=AssetRevisionStatus.created,
            **_stamps(),
        )

    async def rollback(self, asset_id: str, owner_id: str, revision_id: str) -> ModelAsset:
        logger.info(
            "assets.rollback(mock)", asset_id=asset_id, owner_id=owner_id, revision_id=revision_id
        )
        return ModelAsset(
            id=asset_id,
            project_id=gen_uuid(),
            owner_id=owner_id,
            current_revision_id=revision_id,
        )

    async def get_owned_revision_with_asset(
        self, revision_id: str, owner_id: str
    ) -> tuple[AssetRevision, ModelAsset]:
        logger.info(
            "assets.get_owned_revision_with_asset(mock)",
            revision_id=revision_id,
            owner_id=owner_id,
        )
        asset_id = gen_uuid()
        revision = AssetRevision(
            id=revision_id,
            model_asset_id=asset_id,
            artifact_type=ArtifactType.generated_model,
            status=AssetRevisionStatus.created,
        )
        asset = ModelAsset(id=asset_id, project_id=gen_uuid(), owner_id=owner_id)
        return revision, asset

    async def get_current_revision(self, project_id: str, owner_id: str) -> AssetRevision | None:
        logger.info("assets.get_current_revision(mock)", project_id=project_id, owner_id=owner_id)
        return AssetRevision(
            id=gen_uuid(),
            model_asset_id=gen_uuid(),
            artifact_type=ArtifactType.generated_model,
            status=AssetRevisionStatus.printable,
            glb_uri="mock://models/current.glb",
        )

    async def invalidate_revision(self, revision_id: str) -> None:
        logger.info("assets.invalidate_revision(mock)", revision_id=revision_id)
        return None
