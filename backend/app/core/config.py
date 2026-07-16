"""从环境变量和 ``.env`` 加载应用配置。

所有配置只在这里读取，应用其他位置统一导入 ``settings``。解析优先级为：
真实环境变量 > ``.env`` 文件 > 下面的默认值。开发环境保留低门槛默认值，
生产环境则通过 ``_guard_prod_secrets`` 启动时拦截占位密钥，避免服务带着
不安全配置悄悄运行。

当前只保留应用运行与身份认证所需的配置。Redis、对象存储、生成/切片/打印
提供方以及 LLM 相关配置会随对应功能模块的后续 PR 逐步引入。
"""

import ipaddress
import socket
from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 这些占位密钥只允许本地/测试使用，绝不能进入生产环境。
# minioadmin 是 MinIO/对象存储的公开默认凭据，进入 prod 等同于无鉴权。
_INSECURE_DEFAULTS = {"change-me", "change-me-in-prod", "minioadmin"}
_MIN_SECRET_LENGTH = 32

type AppEnv = Literal["local", "test", "prod"]


def _is_local_origin(origin: str) -> bool:
    """判断一个 CORS origin 是否指向本地回环地址。

    解析出 host 后按精确规则判断，而不是子串匹配：``localhost``（含其大小写变体）
    以及所有被归类为回环的 IP（``127.0.0.1``、``127.1``、``[::1]`` 等）都算本地。
    这样既能挡住 ``http://[::1]:3000`` 这类伪装，也不会误杀
    ``https://localhost.example.com`` 这种合法外部域名。
    """
    host = (urlparse(origin).hostname or "").strip().lower()
    if not host:
        return False
    if host == "localhost":
        return True
    # 标准写法（127.0.0.1、::1 等）直接分类。
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        pass
    # 浏览器会把简写 IPv4（如 127.1、127.0.1）规范化为点分四段，ipaddress 不接受这类
    # 简写，需用 inet_aton 展开后再判断，避免 http://127.1 绕过回环校验。
    try:
        expanded = socket.inet_ntoa(socket.inet_aton(host))
    except OSError:
        return False
    return ipaddress.ip_address(expanded).is_loopback


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # 应用基础配置。
    app_env: AppEnv = "local"
    app_debug: bool = True
    app_secret_key: str = "change-me"  # noqa: S105  (开发占位值；生产由 _guard_prod_secrets 拦截)
    app_cors_origins: tuple[str, ...] = ("http://localhost:3000", "http://localhost:5173")
    api_v1_prefix: str = "/api/v1"

    # 数据库。
    database_url: str = "postgresql+asyncpg://xe6:xe6@localhost:5432/xe6"

    # 对象存储（assets 桶）。骨架为 mock，不连接真实 S3/MinIO；这些值供
    # StorageClient 与凭据可观测层读取，证明凭据确实被消费。
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"  # noqa: S105  (开发占位值；生产由 _guard_prod_secrets 拦截)
    s3_bucket: str = "xe6-assets"
    s3_region: str = "us-east-1"

    # 认证：JWT access token 签发参数。
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"

    @model_validator(mode="after")
    def _guard_prod_secrets(self) -> "Settings":
        """生产环境发现占位密钥时立即失败。

        local/test 可以保持零配置默认值；prod 必须显式设置真实密钥。这样错误会暴露在
        启动阶段，而不是等到请求进来后才变成隐蔽的安全问题或调用失败。
        """
        if not self.is_prod:
            return self
        offenders: list[str] = []
        secret = self.app_secret_key.strip()
        if secret in _INSECURE_DEFAULTS or len(secret) < _MIN_SECRET_LENGTH:
            offenders.append(f"APP_SECRET_KEY (minimum {_MIN_SECRET_LENGTH} characters)")
        if self.app_debug:
            offenders.append("APP_DEBUG=false")
        if (
            not self.app_cors_origins
            or "*" in self.app_cors_origins
            or any(_is_local_origin(origin) for origin in self.app_cors_origins)
        ):
            offenders.append("APP_CORS_ORIGINS (explicit allowlist required)")
        # 对象存储占位凭据（minioadmin）进入 prod 等同公开无鉴权，必须显式替换。
        if self.s3_access_key in _INSECURE_DEFAULTS:
            offenders.append("S3_ACCESS_KEY")
        if self.s3_secret_key in _INSECURE_DEFAULTS:
            offenders.append("S3_SECRET_KEY")
        if offenders:
            raise ValueError("Unsafe production settings; set: " + ", ".join(offenders))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
