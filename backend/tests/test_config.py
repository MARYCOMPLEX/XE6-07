import pytest
from pydantic import ValidationError

from app.core.config import Settings


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
    settings = Settings(
        app_env="prod",
        app_debug=False,
        app_secret_key="x" * 32,
        app_cors_origins=("https://app.example.com",),
    )

    assert settings.is_prod
