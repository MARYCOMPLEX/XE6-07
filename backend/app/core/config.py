"""从环境变量和 ``.env`` 加载应用配置。

所有配置只在这里读取，应用其他位置统一导入 ``settings``。解析优先级为：
真实环境变量 > ``.env`` 文件 > 下面的默认值。开发环境保留低门槛默认值，
生产环境则通过 ``_guard_prod_secrets`` 启动时拦截占位密钥，避免服务带着
不安全配置悄悄运行。

基础骨架阶段只保留应用运行必需的最小配置。Redis、对象存储、生成/切片/打印
提供方以及 LLM 相关配置会随对应功能模块的后续 PR 逐步引入。
"""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 这些占位密钥只允许本地/测试使用，绝不能进入生产环境。
_INSECURE_DEFAULTS = {"change-me", "change-me-in-prod"}
_MIN_SECRET_LENGTH = 32
_LOCAL_CORS_HOSTS = ("localhost", "127.0.0.1")

type AppEnv = Literal["local", "test", "prod"]


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
            or any(host in origin for origin in self.app_cors_origins for host in _LOCAL_CORS_HOSTS)
        ):
            offenders.append("APP_CORS_ORIGINS (explicit allowlist required)")
        if offenders:
            raise ValueError("Unsafe production settings; set: " + ", ".join(offenders))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
