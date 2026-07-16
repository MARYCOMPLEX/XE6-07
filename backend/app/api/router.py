"""API v1 聚合路由。

每个功能模块都会暴露自己的 ``router``，由这里收集后交给 ``main.py`` 挂载到版本化
前缀下。后续每个模块 PR 会在这里注册自己的子路由。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.users.router import router as users_router

api_router = APIRouter()

# 认证与账号。
api_router.include_router(users_router)
