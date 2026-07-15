"""API v1 聚合路由。

每个功能模块都会暴露自己的 ``router``，由这里收集后交给 ``main.py`` 挂载到版本化
前缀下。当前基础骨架不含业务模块，聚合路由为空；后续每个模块 PR 会在这里注册
自己的子路由。
"""

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()
