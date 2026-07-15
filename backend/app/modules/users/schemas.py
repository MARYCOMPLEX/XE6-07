"""用户输入输出数据模式，永远不暴露 hashed_password。"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import TimestampedOut


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = None


class UserLogin(BaseModel):
    # 路由使用 OAuth2PasswordRequestForm；这个数据模式用于 JSON 登录。
    username: str
    password: str


class UserUpdate(BaseModel):
    display_name: str | None = None
    avatar_uri: str | None = None


class UserOut(TimestampedOut):
    email: str
    username: str
    role: UserRole
    is_active: bool
    display_name: str | None = None
    avatar_uri: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105  (OAuth2 字段名，不是密钥)
    user: UserOut
