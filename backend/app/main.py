"""FastAPI 应用工厂。

这里负责组装 lifespan、中间件、领域异常处理和版本化 API 路由。业务逻辑全部留在各功能
模块中，本文件只做应用装配。
"""

from __future__ import annotations

import re
import time
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import settings
from app.core.credentials import log_active_credentials
from app.core.exceptions import AppError
from app.core.logging import bind_trace_id, configure_logging, get_logger

logger = get_logger(__name__)

# 入站 x-trace-id 只在匹配这个安全模式时才被信任：长度受限的十六进制/连字符串。
# 客户端可以传入自己的关联 id 以贯穿上下游调用，但不允许注入任意长度或含控制字符、
# 换行的值——否则会污染结构化日志、被回写进响应头，甚至冒用他人的 trace。
_TRACE_ID_RE = re.compile(r"\A[0-9a-zA-Z][0-9a-zA-Z-]{0,63}\Z")


def _safe_trace_id(inbound: str | None) -> str:
    """采纳合法的入站 trace id，否则生成一个服务端 trace id。"""
    if inbound and _TRACE_ID_RE.match(inbound):
        return inbound
    return uuid.uuid4().hex


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """启动与关闭生命周期钩子。"""
    configure_logging(debug=settings.app_debug)
    logger.info("app.startup", env=settings.app_env)
    # 日志配置就绪后立即审计当前进程真正读到的凭据（脱敏），证明配置确实生效。
    log_active_credentials()
    # 后续可在这里预热缓存、确保对象存储桶存在、探测外部提供方可用性。
    yield
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="XE6-07 Backend",
        version="0.1.0",
        docs_url="/docs",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.app_cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_middleware(app)
    _register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def _register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def trace_and_timing(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        trace_id = _safe_trace_id(request.headers.get("x-trace-id"))
        bind_trace_id(trace_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.exception(
                "http.request.failed",
                method=request.method,
                path=request.url.path,
                status=500,
                elapsed_ms=elapsed_ms,
            )
            response = JSONResponse(
                status_code=500,
                content={"error": {"code": "internal_error", "message": "Internal server error"}},
            )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        response.headers["x-trace-id"] = trace_id
        response.headers["x-response-time-ms"] = str(elapsed_ms)
        logger.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            elapsed_ms=elapsed_ms,
        )
        return response


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("app.error", code=exc.code, message=exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )


app = create_app()
