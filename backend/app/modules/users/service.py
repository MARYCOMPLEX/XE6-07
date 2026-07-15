"""用户业务逻辑——骨架 mock 桩版。"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthError
from app.core.logging import get_logger
from app.core.security import create_access_token
from app.models.base import gen_uuid
from app.models.enums import UserRole
from app.models.user import User

from .schemas import UserRegister, UserUpdate

logger = get_logger("users")

# 桩用占位口令散列；骨架不做真实认证，仅需一个非空值填充 ORM 字段。
_MOCK_HASH = "mock-hash"  # noqa: S105  (骨架占位值，非真实凭据)


def _mock_user(**overrides: object) -> User:
    """构造一个字段完整、可直接通过 UserOut 校验的瞬态 mock User。

    真实场景下 role/is_active 由列默认值、created_at/updated_at 由数据库 server_default
    生成；但骨架不落库，瞬态对象这些字段为 None，会导致响应模式校验失败。这里显式补齐，
    等接入真实持久化后本函数整体移除。
    """
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": gen_uuid(),
        "hashed_password": _MOCK_HASH,
        "role": UserRole.user,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return User(**defaults)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(self, data: UserRegister) -> User:
        logger.info("users.register(mock)", email=data.email, username=data.username)
        return _mock_user(
            email=data.email,
            username=data.username,
            display_name=data.display_name,
        )

    async def authenticate(self, username: str, password: str) -> tuple[User, str]:
        # 骨架桩不校验凭据：任意用户名/口令都会签发可用 token。这在生产环境等于
        # 认证绕过，因此显式拒绝——真实认证接入前，mock 登录只允许在非生产环境使用。
        if settings.is_prod:
            raise AuthError("Authentication is not available in this build")
        logger.info("users.authenticate(mock)", username=username)
        user = _mock_user(email=f"{username}@mock", username=username)
        token = create_access_token("mock-user-id", extra={"role": "user"})
        return user, token

    async def get(self, user_id: str) -> User:
        logger.info("users.get(mock)", user_id=user_id)
        return _mock_user(id=user_id, email="mock@mock", username="mock")

    async def update_profile(self, user_id: str, data: UserUpdate) -> User:
        logger.info("users.update_profile(mock)", user_id=user_id)
        user = _mock_user(id=user_id, email="mock@mock", username="mock")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        return user
