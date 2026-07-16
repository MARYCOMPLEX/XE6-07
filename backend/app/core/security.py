"""密码哈希与 JWT access token。"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthError

# 默认用 bcrypt_sha256：先对口令做 SHA256 再交给 bcrypt，彻底消除 bcrypt 仅取前 72
# 字节的静默截断（否则 "a"*72+"X" 与 "a"*72+"Y" 会互相通过校验，多字节字符更早触发）。
# 保留裸 bcrypt 仅用于校验历史哈希；新哈希一律走 bcrypt_sha256。
_pwd = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


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
