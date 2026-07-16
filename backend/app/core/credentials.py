"""凭据可观测层：证明服务"确实"读取并使用了配置里的凭据。

骨架模式下所有外部执行都被 mock 替换，但我们仍然要能在日志里看到：

  1. 启动时——当前进程真正从 ``settings`` 读到的全部凭据（``log_active_credentials``）；
  2. 调用时——每一步 mock 执行实际消费了哪条凭据（``log_credential_use``）。

敏感值统一脱敏：只保留头尾字符，中间用 ``***`` 遮盖，既能证明"读到了非空值"，
又不会把密钥明文写进日志。
"""

from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("credentials")


def mask(value: str | None) -> str:
    """脱敏一个凭据值，保留头尾以便肉眼核对，中间遮盖。"""
    if not value:
        return "<empty>"
    text = str(value)
    if len(text) <= 4:
        return "***"
    if len(text) <= 8:
        return f"{text[:1]}***{text[-1:]}"
    return f"{text[:3]}***{text[-3:]}"


# 凭据登记表：名称 -> (取值函数, 是否敏感)。
# 新增真实凭据时在这里登记一行，启动日志与调用日志都会自动覆盖。
_REGISTRY: dict[str, tuple[str, bool]] = {
    "app_secret_key": ("APP_SECRET_KEY", True),
    "database_url": ("DATABASE_URL", True),
    # 对象存储（assets 桶）。后续 provider 桶（生成、切片、打印、LLM 等）接入时
    # 在此登记自己的凭据行，启动日志与调用日志会自动覆盖。
    "s3_endpoint_url": ("S3_ENDPOINT_URL", False),
    "s3_access_key": ("S3_ACCESS_KEY", True),
    "s3_secret_key": ("S3_SECRET_KEY", True),
    "s3_bucket": ("S3_BUCKET", False),
    "s3_region": ("S3_REGION", False),
}


def _display(attr: str, sensitive: bool) -> str:
    raw = getattr(settings, attr, None)
    return mask(raw) if sensitive else (str(raw) if raw not in (None, "") else "<empty>")


def log_active_credentials() -> None:
    """启动时打印当前进程真正读到的全部凭据（脱敏）。"""
    logger.info("credentials.loaded", env=settings.app_env, count=len(_REGISTRY))
    for attr, (env_name, sensitive) in _REGISTRY.items():
        logger.info(
            "credentials.active",
            key=env_name,
            value=_display(attr, sensitive),
            sensitive=sensitive,
        )


def log_credential_use(*attrs: str, purpose: str) -> None:
    """在一次 mock 执行处记录"这一步确实消费了这些凭据"。

    ``attrs`` 是 ``settings`` 上的属性名，例如 ``"llm_api_key"``、``"s3_access_key"``。
    日志会带上脱敏后的值，证明调用点确实读到了配置值，而不是空跑。
    """
    used = {}
    for attr in attrs:
        env_name, sensitive = _REGISTRY.get(attr, (attr.upper(), True))
        used[env_name] = _display(attr, sensitive)
    logger.info("credentials.used", purpose=purpose, **used)


__all__ = ["log_active_credentials", "log_credential_use", "mask"]
