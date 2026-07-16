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

    @staticmethod
    def _guard_prod() -> None:
        # 整个 service 都是不落库的 mock 桩：生产环境下 register/authenticate/get/
        # update_profile 都会“返回成功但静默丢弃数据”，等于认证绕过 + 数据丢失。
        # 真实持久化接入前，统一禁止生产环境使用本模块的任何 mock 路由。
        if settings.is_prod:
            raise AuthError("User service is not available in this build")

    async def register(self, data: UserRegister) -> User:
        self._guard_prod()
        logger.info("users.register(mock)", email=data.email, username=data.username)
        return _mock_user(
            email=data.email,
            username=data.username,
            display_name=data.display_name,
        )

    async def authenticate(self, username: str, password: str) -> tuple[User, str]:
        self._guard_prod()
        logger.info("users.authenticate(mock)", username=username)
        user = _mock_user(email=f"{username}@mock", username=username)
        # token 的 sub 必须等于返回给客户端的 user.id：登录响应、JWT sub、后续 /me
        # 三者身份要一致，否则客户端会在登录后发生身份切换。role 也取自该用户。
        token = create_access_token(user.id, extra={"role": user.role.value})
        return user, token

    async def get(self, user_id: str, *, role: UserRole = UserRole.user) -> User:
        self._guard_prod()
        logger.info("users.get(mock)", user_id=user_id)
        # role 取自调用方的已认证身份（JWT），否则 admin 请求 /me 会被降级成 user。
        return _mock_user(id=user_id, email="mock@mock", username="mock", role=role)

    async def update_profile(
        self, user_id: str, data: UserUpdate, *, role: UserRole = UserRole.user
    ) -> User:
        self._guard_prod()
        logger.info("users.update_profile(mock)", user_id=user_id)
        user = _mock_user(id=user_id, email="mock@mock", username="mock", role=role)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        return user
