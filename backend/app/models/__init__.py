"""ORM 模型注册入口。

导入本包会把模型挂到 ``Base.metadata``，供 Alembic autogenerate 和 ``create_all``
发现完整 schema。后续每个模块 PR 会在这里注册自己的模型。
"""

from __future__ import annotations

from app.models.asset import AssetRevision, MeshReport, ModelAsset
from app.models.base import Base
from app.models.generation import GeneratedImage, GenerationJob
from app.models.project import (
    ChatMessage,
    DesignIntent,
    Project,
    SessionContext,
)
from app.models.user import User

__all__ = [
    "Base",
    # 用户（#151）。
    "User",
    # 项目工作台（工作流桶）。
    "Project",
    "SessionContext",
    "DesignIntent",
    "ChatMessage",
    # 生成（工作流桶）。
    "GenerationJob",
    "GeneratedImage",
    # 资产与模型版本（本 PR）。
    "ModelAsset",
    "AssetRevision",
    "MeshReport",
]
