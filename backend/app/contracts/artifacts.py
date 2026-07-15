"""可安全跨模块、跨进程传递的产物引用。"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

from app.contracts import FrozenContract


class ArtifactKind(StrEnum):
    """流水线中带版本的二进制产物或报告类型。"""

    reference_image = "reference_image"
    model_glb = "model_glb"
    model_stl = "model_stl"
    model_3mf = "model_3mf"
    gcode = "gcode"
    slice_report = "slice_report"
    mesh_report = "mesh_report"
    other = "other"


class ArtifactRef(FrozenContract):
    """不透明产物身份与稳定元数据。

    ``artifact_id`` 是模块间传递的稳定身份。下载地址、存储 key、提供方名称与凭据
    均不进入这个契约；客户端访问地址只在完成授权校验后的 API 响应边界临时签发。
    """

    artifact_id: str
    kind: ArtifactKind
    media_type: str | None = None
    checksum_sha256: str | None = None
    size_bytes: int | None = None
    simulated: bool = False
    metadata: Mapping[str, object] | None = None


__all__ = ["ArtifactKind", "ArtifactRef"]
