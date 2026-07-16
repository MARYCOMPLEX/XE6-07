"""模型资产、版本和网格报告的数据访问。"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.asset import AssetRevision, MeshReport, ModelAsset
from app.repositories.base import BaseRepository


class ModelAssetRepository(BaseRepository[ModelAsset]):
    model = ModelAsset

    async def get_with_revisions(self, asset_id: str) -> ModelAsset | None:
        stmt = (
            select(ModelAsset)
            .where(ModelAsset.id == asset_id)
            .options(selectinload(ModelAsset.revisions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_project(
        self, project_id: str, *, offset: int, limit: int
    ) -> Sequence[ModelAsset]:
        return await self.list(project_id=project_id, offset=offset, limit=limit)


class RevisionRepository(BaseRepository[AssetRevision]):
    model = AssetRevision

    async def list_for_asset(self, asset_id: str) -> Sequence[AssetRevision]:
        return await self.list(model_asset_id=asset_id, limit=200)


class MeshReportRepository(BaseRepository[MeshReport]):
    model = MeshReport

    async def latest_for_revision(self, revision_id: str) -> MeshReport | None:
        stmt = (
            select(MeshReport)
            .where(MeshReport.revision_id == revision_id)
            .order_by(MeshReport.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_stale_for_revision(self, revision_id: str) -> None:
        """几何变化时让旧报告失效。"""
        reports = await self.list(revision_id=revision_id, limit=200)
        for r in reports:
            r.is_stale = True
        await self.session.flush()
