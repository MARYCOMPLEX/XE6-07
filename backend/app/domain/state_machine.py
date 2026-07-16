"""项目状态有限状态机：项目流转的权威守卫。

按照产品规则，Agent 只负责提出“用户想做什么”，状态机负责判断“当前能不能做”。
本文件保持纯领域逻辑，不依赖数据库、LLM 或 Web 框架，因此完整流转表可以被
单元测试独立覆盖。

用法：
    guard = ProjectStateMachine()
    guard.assert_can(current, target)          # 不合法时抛 InvalidStateTransitionError
    guard.allowed_next(current)                # 返回当前状态允许进入的下一组状态
"""

from __future__ import annotations

from app.core.exceptions import InvalidStateTransitionError
from app.models.enums import ProjectStatus as S

# 有向邻接表：每个状态对应它可以合法进入的下一批状态。
# 这里承接产品主流程，同时保留修订、失败、归档这几个兜底出口。
_TRANSITIONS: dict[S, set[S]] = {
    S.draft: {S.input_received, S.archived},
    S.input_received: {S.intent_confirming, S.model_normalizing, S.archived},
    S.intent_confirming: {S.intent_confirmed, S.intent_confirming, S.failed},
    S.intent_confirmed: {S.design_selecting, S.generating_image, S.failed},
    S.design_selecting: {S.generating_image, S.generating_model, S.revising},
    S.generating_image: {S.reference_image_ready, S.failed},
    S.reference_image_ready: {S.generating_model, S.design_selecting, S.revising},
    S.generating_model: {S.reviewing_model, S.failed},
    S.reviewing_model: {S.model_normalizing, S.generating_model, S.revising},
    S.model_normalizing: {S.printability_checking, S.failed},
    S.printability_checking: {S.needs_repair, S.ready_to_slice, S.failed},
    S.needs_repair: {S.repairing, S.revising},
    S.repairing: {S.printability_checking, S.failed},  # 修复完成后必须重新审计。
    S.ready_to_slice: {S.slicing, S.revising},
    S.slicing: {S.ready_to_print, S.failed},
    S.ready_to_print: {S.queued, S.revising},
    S.queued: {S.printing, S.revising, S.failed},
    S.printing: {S.paused, S.completed, S.failed},
    S.paused: {S.printing, S.failed},
    S.completed: {S.picked_up, S.revising},
    S.picked_up: {S.revising, S.archived},
    # 修订态可以回到重新生成、重新修复或重新切片等入口。
    S.revising: {
        S.design_selecting,
        S.generating_image,
        S.generating_model,
        S.repairing,
        S.ready_to_slice,
        S.slicing,
        S.archived,
    },
    S.failed: {S.revising, S.archived},
    S.archived: set(),
}

# 几乎所有状态都可以进入的全局出口。
_GLOBAL: set[S] = {S.failed, S.archived}

# 普通客户端只允许提交这些“用户确实有权决定”的目标状态。
# 外部提供方和任务的执行结果必须通过可信 WorkflowEvent 进入，避免前端伪造异步结果。
_USER_COMMAND_TARGETS: set[S] = {
    S.input_received,
    S.intent_confirmed,
    S.design_selecting,
    S.revising,
    S.archived,
}


class ProjectStateMachine:
    """围绕 :class:`ProjectStatus` 的纯状态流转守卫。"""

    transitions = _TRANSITIONS

    def allowed_next(self, current: S) -> set[S]:
        if current is S.archived:
            return set()
        return self.transitions.get(current, set()) | _GLOBAL

    def can(self, current: S, target: S) -> bool:
        if current == target:
            return True  # 幂等空操作：重复应用同一状态不算非法。
        return target in self.allowed_next(current)

    def can_user_command(self, current: S, target: S) -> bool:
        return target in _USER_COMMAND_TARGETS and self.can(current, target)

    def is_user_command_target(self, target: S) -> bool:
        """目标是否属于用户可直接命令的状态（与当前状态无关的必要条件）。

        系统结果态（如 ``generating_image``）不在此集合，只能经可信 WorkflowEvent 进入。
        骨架桩不持有当前状态，用它先挡住"客户端伪造系统结果态"这条契约级红线。
        """
        return target in _USER_COMMAND_TARGETS

    def assert_can(self, current: S, target: S) -> None:
        if not self.can(current, target):
            raise InvalidStateTransitionError(
                f"Cannot move project from {current.value!r} to {target.value!r}",
            )


state_machine = ProjectStateMachine()
