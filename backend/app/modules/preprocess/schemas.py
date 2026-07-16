"""模型预处理与后处理数据模式。

预处理在模型首次进入流水线时执行，用于单位、坐标、尺度、朝向和碎片清理。后处理在输出前
执行，例如简化、空心、加底座、加孔、加厚、切平底。任何改变几何的处理都会产生新的
AssetRevision，并让旧审计/切片结果失效，因此调用方需要重新审计。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import JobStatus
from app.schemas.common import ORMModel, TimestampedOut

# MeshAdapter 必须实现的操作名。这里保持封闭集合，避免 API 面被动态扩张，
# 也避免 LLM 发明未受控的物理几何操作。
PreOp = Literal[
    "normalize_units",  # 推断或转换为 mm。
    "recenter",  # 移动到原点或构建板中心。
    "orient",  # 放到最大平面朝下的姿态。
    "remove_fragments",  # 删除断开的碎片壳。
    "recompute_normals",
]
_DEFAULT_PRE_OPS: list[PreOp] = ["normalize_units", "recenter"]
PostOp = Literal[
    "decimate",  # 降低面数。
    "thicken",  # 满足最小壁厚。
    "add_base",  # 添加适合 raft/brim 的平底。
    "add_hole",  # 添加钥匙扣孔。
    "cut_flat",  # 切出平底。
    "hollow",  # 空心化以节省材料。
]


class PreprocessRequest(BaseModel):
    """对刚进入流水线的模型版本做规范化。"""

    revision_id: str
    ops: list[PreOp] = Field(default_factory=lambda: _DEFAULT_PRE_OPS.copy())
    params: dict[str, Any] = Field(default_factory=dict)


class PostprocessRequest(BaseModel):
    """输出前几何编辑；会产生新的模型版本。"""

    revision_id: str
    ops: list[PostOp] = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


class ProcessAccepted(ORMModel):
    """202 响应载荷：处理异步执行，完成后产出新版本。"""

    job_ref: str
    source_revision_id: str
    status: JobStatus


class ProcessResult(TimestampedOut):
    source_revision_id: str
    new_revision_id: str | None = None
    applied_ops: list[str] = Field(default_factory=list)
    status: JobStatus
    error_message: str | None = None
