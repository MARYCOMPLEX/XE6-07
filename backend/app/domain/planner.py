"""Agent 动作规划器：位于“意图提案”和“真实执行”之间的确定性关口。

这里是“Agent 提议，FSM 决策”规则的代码化表达。Agent 先把用户输入识别成
:class:`IntentType`，规划器再从领域规则角度判断该意图在当前状态下是否允许：

  1. 将 intent 映射到它希望推进到的 ``ProjectStatus``；
  2. 询问状态机该流转是否合法；
  3. 返回可执行步骤（服务动作 + 目标状态），或返回包含原因和合法下一步的拒绝。

本模块保持纯函数形态，不接触数据库、LLM 或框架。这样意图决策表可以独立测试，
服务层也不会绕过这个关口直接执行危险动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.state_machine import state_machine
from app.models.enums import IntentType
from app.models.enums import ProjectStatus as S

# 不推进流水线的对话类意图：始终允许，不改变项目状态。
_CONVERSATIONAL: set[IntentType] = {
    IntentType.chat,
    IntentType.inspiration,
    IntentType.community_search,
    IntentType.query_status,
}

# 用户意图到目标项目状态的唯一映射表；对话类意图不会进入这里，因为它们不流转。
_INTENT_GOAL: dict[IntentType, S] = {
    IntentType.clarify_intent: S.intent_confirming,
    IntentType.generate_image: S.generating_image,
    IntentType.generate_model: S.generating_model,
    IntentType.import_model: S.model_normalizing,
    IntentType.audit_model: S.printability_checking,
    IntentType.repair_model: S.repairing,
    IntentType.slice_model: S.slicing,
    IntentType.confirm_print: S.queued,
    IntentType.cancel: S.revising,
}

# 面向服务和工具层的动作名，后续会被映射为具体服务调用。
_INTENT_ACTION: dict[IntentType, str] = {
    IntentType.clarify_intent: "clarify_intent",
    IntentType.generate_image: "text_to_image",
    IntentType.generate_model: "image_to_model",
    IntentType.import_model: "normalize_model",
    IntentType.audit_model: "audit",
    IntentType.repair_model: "postprocess",
    IntentType.slice_model: "slice",
    IntentType.confirm_print: "submit_print",
    IntentType.cancel: "cancel",
}


@dataclass(frozen=True)
class ExecutableStep:
    """已通过领域规则的动作：包含要执行的服务动作和目标状态。"""

    intent: IntentType
    action: str
    goal_state: S | None  # 对话类意图不流转，因此目标状态为空。
    conversational: bool = False


@dataclass(frozen=True)
class Rejection:
    """被领域规则拦下的动作，携带拒绝原因和可选合法下一步。"""

    intent: IntentType
    reason: str
    current_state: S
    allowed_next: list[S] = field(default_factory=list)


def plan(intent: IntentType, current: S) -> ExecutableStep | Rejection:
    """判断 ``intent`` 在 ``current`` 项目状态下是否允许执行。

    合法时返回服务层可执行的 :class:`ExecutableStep`；不合法时返回
    :class:`Rejection`，让上层能向用户解释原因并展示合法下一步。
    """
    # 对话类意图不触碰流水线。
    if intent in _CONVERSATIONAL:
        return ExecutableStep(
            intent=intent, action=intent.value, goal_state=None, conversational=True
        )

    goal = _INTENT_GOAL.get(intent)
    if goal is None:  # pragma: no cover - 封闭枚举下的防御分支。
        return Rejection(
            intent=intent,
            reason=f"未知意图 {intent.value!r}，无法映射到流程动作。",
            current_state=current,
            allowed_next=sorted(state_machine.allowed_next(current), key=lambda s: s.value),
        )

    if not state_machine.can(current, goal):
        return Rejection(
            intent=intent,
            reason=(
                f"当前处于 {current.value!r}，还不能执行 {intent.value!r}"
                f"（需要先到达 {goal.value!r} 的前置状态）。"
            ),
            current_state=current,
            allowed_next=sorted(state_machine.allowed_next(current), key=lambda s: s.value),
        )

    return ExecutableStep(
        intent=intent,
        action=_INTENT_ACTION[intent],
        goal_state=goal,
        conversational=False,
    )
