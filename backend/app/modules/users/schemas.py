"""用户输入输出数据模式，永远不暴露 hashed_password。"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import TimestampedOut


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    # 与 User.display_name 列 String(128) 对齐，避免接入真实库后写入失败/截断。
    display_name: str | None = Field(default=None, max_length=128)


class UserLogin(BaseModel):
    # 路由使用 OAuth2PasswordRequestForm；这个数据模式用于 JSON 登录。
    username: str
    password: str


class UserUpdate(BaseModel):
    # 与 User 列长度对齐：display_name String(128)、avatar_uri String(512)。
    display_name: str | None = Field(default=None, max_length=128)
    avatar_uri: str | None = Field(default=None, max_length=512)


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
