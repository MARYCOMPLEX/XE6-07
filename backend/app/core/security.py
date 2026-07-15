"""密码哈希与 JWT access token。"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthError

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw: str) -> str:
    return _pwd.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _pwd.verify(raw, hashed)


# 由本函数独占设置的保留声明，调用方不得通过 extra 覆盖，否则可能签发指向
# 非预期身份或非预期有效期的 token。
_RESERVED_CLAIMS = frozenset({"sub", "exp"})


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    if extra:
        conflicting = _RESERVED_CLAIMS & extra.keys()
        if conflicting:
            raise ValueError(f"extra 不能覆盖保留声明: {sorted(conflicting)}")
    # 先放入自定义声明，再写入受控的 sub/exp，双重保证保留声明不被覆盖。
    payload: dict[str, Any] = {**(extra or {})}
    payload["sub"] = subject
    payload["exp"] = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.app_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise AuthError("Invalid or expired token") from exc
