"""共享 FastAPI 依赖：数据库会话与认证/授权。

基础骨架阶段只提供身份模块所需的依赖。存储、Agent 运行时、分页等依赖会随
对应模块 PR 追加。
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.exceptions import AuthError, PermissionDeniedError
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/users/login", auto_error=False
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


class CurrentUser(BaseModel):
    id: str
    role: str = "user"


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> CurrentUser:
    if not token:
        raise AuthError("Authentication required")
    payload = decode_access_token(token)
    sub = payload.get("sub")
    if not sub:
        raise AuthError("Invalid token subject")
    return CurrentUser(id=sub, role=payload.get("role", "user"))


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


async def require_admin(user: CurrentUserDep) -> CurrentUser:
    if user.role != "admin":
        raise PermissionDeniedError("Admin privileges required")
    return user


AdminDep = Annotated[CurrentUser, Depends(require_admin)]
