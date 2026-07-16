"""API v1 聚合路由。

每个功能模块都会暴露自己的 ``router``，由这里收集后交给 ``main.py`` 挂载到版本化
前缀下。后续每个模块 PR 会在这里注册自己的子路由。
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.assets.router import router as assets_router
from app.modules.generation.router import router as generation_router
from app.modules.projects.router import router as projects_router
from app.modules.users.router import router as users_router

api_router = APIRouter()

# 认证与账号。
api_router.include_router(users_router)
# 工作台：项目、对话、设计意图。
api_router.include_router(projects_router)
# 生成相关：文生图、图生图、图生模型、意图识别。
api_router.include_router(generation_router)
# 资产与模型版本：模型资产、修订、网格报告、回滚。
api_router.include_router(assets_router)
