"""模型和数据模式共享的领域枚举。

枚举值是稳定的存储和接口值。身份模块的用户词表随 #151 落地；工作流桶追加项目状态机、
会话状态、来源类型、任务/生成词表与 Agent 意图集合；本 PR（资产）追加资产版本状态、
产物类型与可见性。社区、打印等其余枚举会随对应模块 PR 继续追加。
"""

from __future__ import annotations

import enum


# 对齐 #129：本期只设普通用户与统一管理员两类身份。后续如需拆分
# （content_reviewer / printer_operator / account_admin 等）再在此扩展，
# 已有业务结果不受影响。
class UserRole(enum.StrEnum):
    user = "user"
    admin = "admin"


class SessionState(enum.StrEnum):
    CHAT = "CHAT"
    INSPIRATION = "INSPIRATION"
    COMMUNITY_SEARCH = "COMMUNITY_SEARCH"
    INTENT_CONFIRMING = "INTENT_CONFIRMING"
    PRINT_JOB_ACTIVE = "PRINT_JOB_ACTIVE"


class ProjectStatus(enum.StrEnum):
    draft = "draft"
    input_received = "input_received"
    intent_confirming = "intent_confirming"
    intent_confirmed = "intent_confirmed"
    design_selecting = "design_selecting"
    generating_image = "generating_image"
    reference_image_ready = "reference_image_ready"
    generating_model = "generating_model"
    reviewing_model = "reviewing_model"
    model_normalizing = "model_normalizing"
    printability_checking = "printability_checking"
    needs_repair = "needs_repair"
    repairing = "repairing"
    ready_to_slice = "ready_to_slice"
    slicing = "slicing"
    ready_to_print = "ready_to_print"
    queued = "queued"
    printing = "printing"
    paused = "paused"
    completed = "completed"
    picked_up = "picked_up"
    revising = "revising"
    failed = "failed"
    archived = "archived"


class SourceType(enum.StrEnum):
    text = "text"
    image = "image"
    upload = "upload"
    community = "community"


class AssetRevisionStatus(enum.StrEnum):
    created = "created"
    preview_ready = "preview_ready"
    audit_pending = "audit_pending"
    printable = "printable"
    not_printable = "not_printable"
    repaired = "repaired"
    sliced = "sliced"
    deprecated = "deprecated"
    exported = "exported"


class ArtifactType(enum.StrEnum):
    reference_image = "reference_image"
    generated_model = "generated_model"
    uploaded_model = "uploaded_model"
    repaired_model = "repaired_model"
    sliced = "sliced"
    exported = "exported"


class Visibility(enum.StrEnum):
    private = "private"
    public = "public"
    unlisted = "unlisted"


class JobStatus(enum.StrEnum):
    pending = "pending"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    timeout = "timeout"


class GenerationKind(enum.StrEnum):
    text_to_image = "text_to_image"
    image_to_images = "image_to_images"
    image_to_model = "image_to_model"
    text_to_model = "text_to_model"


class IntentType(enum.StrEnum):
    """Agent 可识别的用户意图集合。

    Agent 只把自由输入映射到这些意图之一；是否允许执行由 planner 决定。保持封闭集合，
    可以防止 LLM 发明系统没有规则的动作。
    """

    chat = "chat"  # 普通问答或概念解释。
    inspiration = "inspiration"  # 用户还不知道打印什么时的灵感建议。
    community_search = "community_search"
    clarify_intent = "clarify_intent"  # 补齐缺失设计字段。
    generate_image = "generate_image"  # 文本生成参考图。
    generate_model = "generate_model"  # 图片生成 3D 模型。
    import_model = "import_model"  # 已上传模型进入规范化流程。
    audit_model = "audit_model"  # 可打印性审计。
    repair_model = "repair_model"  # 轻量网格修复。
    slice_model = "slice_model"  # 对可打印版本切片。
    confirm_print = "confirm_print"  # 确认清单并提交打印。
    query_status = "query_status"  # 查询项目或打印状态。
    cancel = "cancel"
