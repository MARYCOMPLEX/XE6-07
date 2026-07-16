"""ORM 模型注册入口。

导入本包会把模型挂到 ``Base.metadata``，供 Alembic autogenerate 和 ``create_all``
发现完整 schema。后续每个模块 PR 会在这里注册自己的模型。
"""

from __future__ import annotations

from app.models.asset import AssetRevision, MeshReport, ModelAsset
from app.models.base import Base
from app.models.generation import GeneratedImage, GenerationJob
from app.models.print import (
    MaterialSpool,
    PrintChecklist,
    PrinterDevice,
    PrintJob,
    SliceJob,
)
from app.models.project import (
    ChatMessage,
    DesignIntent,
    Project,
    SessionContext,
)
from app.models.user import User
from app.models.workflow import MeshProcessJob, WorkflowEventReceipt

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
    # 资产与模型版本（资产桶）。
    "ModelAsset",
    "AssetRevision",
    "MeshReport",
    # 预处理与工作流回执（本 PR）。
    "MeshProcessJob",
    "WorkflowEventReceipt",
    # 设备、切片与打印（本 PR）。
    "PrinterDevice",
    "MaterialSpool",
    "SliceJob",
    "PrintChecklist",
    "PrintJob",
]
