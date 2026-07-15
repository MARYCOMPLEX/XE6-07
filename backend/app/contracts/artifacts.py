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
    gcode = "gcode"
    slice_report = "slice_report"
    mesh_report = "mesh_report"
    other = "other"


class ArtifactRef(FrozenContract):
    """不透明产物身份，以及可选的客户端安全下载地址。

    ``artifact_id`` 是模块间传递的稳定身份。存储 key 与提供方凭据故意不进入
    这个契约，避免异步事件和业务模块泄露底层存储实现。
    """

    artifact_id: str
    kind: ArtifactKind
    download_url: str | None = None
    media_type: str | None = None
    checksum_sha256: str | None = None
    size_bytes: int | None = None
    provider: str | None = None
    simulated: bool = False
    metadata: Mapping[str, object] | None = None


__all__ = ["ArtifactKind", "ArtifactRef"]
