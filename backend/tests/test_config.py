from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


def _safe_prod(**overrides: object) -> dict[str, object]:
    """一份能通过 prod 守卫的最小合法配置，逐项破坏用于负例。"""
    base: dict[str, object] = {
        "app_env": "prod",
        "app_debug": False,
        "app_secret_key": "x" * 40,
        "app_cors_origins": ("https://app.example.com",),
        "s3_access_key": "real-access-key",
        "s3_secret_key": "real-secret-key",
    }
    base.update(overrides)
    return base


def test_prod_rejects_debug_mode() -> None:
    with pytest.raises(ValidationError, match="APP_DEBUG=false"):
        Settings(app_env="prod", app_secret_key="x" * 32)


@pytest.mark.parametrize("secret", ["", "short", "change-me", "change-me-in-prod"])
def test_prod_rejects_weak_secrets(secret: str) -> None:
    with pytest.raises(ValidationError, match="APP_SECRET_KEY"):
        Settings(app_env="prod", app_debug=False, app_secret_key=secret)


def test_prod_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="APP_CORS_ORIGINS"):
        Settings(
            app_env="prod",
            app_debug=False,
            app_secret_key="x" * 32,
            app_cors_origins=("*",),
        )


def test_prod_rejects_default_local_cors_origins() -> None:
    with pytest.raises(ValidationError, match="APP_CORS_ORIGINS"):
        Settings(app_env="prod", app_debug=False, app_secret_key="x" * 32)


def test_prod_accepts_explicit_safe_settings() -> None:
    settings = Settings(**_safe_prod())

    assert settings.is_prod


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:3000",
        "http://LOCALHOST:3000",
        "http://127.0.0.1:8000",
        "http://127.1:3000",  # 简写 IPv4，浏览器会规范化为 127.0.0.1
        "http://[::1]:3000",  # IPv6 回环
    ],
)
def test_prod_rejects_loopback_cors_origins(origin: str) -> None:
    with pytest.raises(ValidationError, match="APP_CORS_ORIGINS"):
        Settings(
            app_env="prod",
            app_debug=False,
            app_secret_key="x" * 32,
            app_cors_origins=(origin,),
        )


def test_prod_accepts_external_domain_containing_localhost() -> None:
    # 子串匹配会把它误判为本地；正确的 host 解析应放行这个合法外部域名。
    settings = Settings(**_safe_prod(app_cors_origins=("https://localhost.example.com",)))

    assert settings.is_prod


# ── #158 复审：对象存储凭据与启动审计 ─────────────────────────────────


def test_prod_rejects_default_s3_secret() -> None:
    """prod 带 minioadmin 默认 S3 密钥必须启动失败（等同公开无鉴权）。"""
    with pytest.raises(ValidationError, match="S3_SECRET_KEY"):
        Settings(**_safe_prod(s3_secret_key="minioadmin"))


def test_prod_rejects_default_s3_access_key() -> None:
    with pytest.raises(ValidationError, match="S3_ACCESS_KEY"):
        Settings(**_safe_prod(s3_access_key="minioadmin"))


def test_local_allows_default_s3_credentials() -> None:
    """local 保持零配置：默认 minioadmin 不拦截。"""
    settings = Settings(app_env="local")
    assert settings.s3_secret_key == "minioadmin"


def test_lifespan_invokes_credential_audit() -> None:
    """启动 lifespan 必须实际调用凭据审计，否则 credentials.py 形同虚设。"""
    with (
        patch("app.main.log_active_credentials") as audit,
        TestClient(create_app()),
    ):
        pass
    audit.assert_called_once()
