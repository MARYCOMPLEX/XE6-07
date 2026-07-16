"""模型和数据模式共享的领域枚举。

枚举值是稳定的存储和接口值。基础骨架只包含身份模块所需的用户词表；
其余模块（项目状态机、资产版本、任务、社区等）的枚举会随对应模块 PR 追加。
"""

from __future__ import annotations

import enum


# 对齐 #129：本期只设普通用户与统一管理员两类身份。后续如需拆分
# （content_reviewer / printer_operator / account_admin 等）再在此扩展，
# 已有业务结果不受影响。
class UserRole(enum.StrEnum):
    user = "user"
    admin = "admin"
