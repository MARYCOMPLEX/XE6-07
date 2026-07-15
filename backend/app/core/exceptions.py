"""领域级异常，会在 main.py 中统一映射为 HTTP 响应。"""

from __future__ import annotations


class AppError(Exception):
    """应用异常基类。"""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class PermissionDeniedError(AppError):
    status_code = 403
    code = "permission_denied"


class AuthError(AppError):
    status_code = 401
    code = "unauthorized"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class InvalidStateTransitionError(AppError):
    """状态机拒绝某次流转请求时抛出。"""

    status_code = 409
    code = "invalid_state_transition"


class UnknownProviderError(AppError):
    """请求的适配器提供方未显式注册时抛出。"""

    status_code = 422
    code = "unknown_provider"

    def __init__(self, kind: str, provider: str, available: tuple[str, ...]) -> None:
        self.kind = kind
        self.provider = provider
        self.available = available
        choices = ", ".join(available) if available else "none"
        super().__init__(
            f"Unknown {kind} provider {provider!r}; registered providers: {choices}",
        )
