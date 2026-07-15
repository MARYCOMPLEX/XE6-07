"""结构化日志与请求级 trace id。"""

import logging
import sys
import uuid
from collections.abc import Mapping, MutableMapping, Sequence
from contextvars import ContextVar
from typing import Any

import structlog

trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")

_FIELD_ORDER = ("method", "path", "status", "elapsed", "trace_id")
_FIELD_WIDTHS = {
    "method": 11,
    "path": 28,
    "status": 10,
    "elapsed": 14,
    "trace_id": 42,
}
_RESET = "\033[0m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"
_BOLD = "\033[1m"


def bind_trace_id(trace_id: str | None = None) -> str:
    tid = trace_id or uuid.uuid4().hex
    trace_id_ctx.set(tid)
    return tid


def _add_trace_id(
    _: Any, __: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    if tid := trace_id_ctx.get():
        event_dict["trace_id"] = tid
    return event_dict


def _format_http_fields(
    _: Any, __: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """规范化请求日志字段，让本地控制台输出更容易横向扫描。"""
    if "elapsed_ms" in event_dict:
        event_dict["elapsed"] = f"{int(event_dict.pop('elapsed_ms'))}ms"
    return event_dict


def _shared_processors() -> Sequence[structlog.typing.Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        _add_trace_id,
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _format_http_fields,
    ]


def _renderer(debug: bool) -> structlog.typing.Processor:
    if debug:
        return _FixedWidthConsoleRenderer()
    return structlog.processors.JSONRenderer()


class _FixedWidthConsoleRenderer:
    """将本地日志渲染成固定宽度、用竖线分隔的行。"""

    timestamp_width = 27
    level_width = 7
    logger_width = 13
    event_width = 28

    def __call__(
        self,
        _: Any,
        __: str,
        event_dict: MutableMapping[str, Any],
    ) -> str:
        timestamp = _clip(str(event_dict.pop("timestamp", "")), self.timestamp_width)
        level = _clip(str(event_dict.pop("level", "")).upper(), self.level_width)
        logger_name = _display_logger(str(event_dict.pop("logger", "")))
        logger_name = _clip(logger_name, self.logger_width)
        event = _clip(str(event_dict.pop("event", "")), self.event_width)
        fields = _render_fields(event_dict)
        timestamp_cell = _ansi_cell(timestamp, self.timestamp_width, _DIM)
        level_cell = _ansi_cell(level, self.level_width, _level_color(level))
        logger_cell = _ansi_cell(logger_name, self.logger_width, _BLUE)
        event_cell = _ansi_cell(event, self.event_width, _BOLD)
        return f"{timestamp_cell} | {level_cell} | {logger_cell} | {event_cell} | {fields}".rstrip()


def _display_logger(name: str) -> str:
    if name == "uvicorn.error":
        return "uvicorn"
    return name or "-"


def _render_fields(fields: Mapping[str, Any]) -> str:
    ordered = [(key, fields[key]) for key in _FIELD_ORDER if key in fields]
    ordered.extend((key, value) for key, value in fields.items() if key not in _FIELD_ORDER)
    return " | ".join(_render_field(key, value) for key, value in ordered)


def _render_field(key: str, value: Any) -> str:
    width = _FIELD_WIDTHS.get(key, 18)
    key_label = f"{key}="
    value_width = max(width - len(key_label), 1)
    value_text = f"{_clip(str(value), value_width):<{value_width}}"
    return f"{_color(key_label, _CYAN)}{_color(value_text, _value_color(key, value))}"


def _level_color(level: str) -> str:
    normalized = level.lower()
    if normalized in {"error", "critical"}:
        return _RED + _BOLD
    if normalized == "warning":
        return _YELLOW
    if normalized == "info":
        return _GREEN
    return _MAGENTA


def _value_color(key: str, value: Any) -> str:
    if key == "status":
        try:
            status = int(value)
        except (TypeError, ValueError):
            return _MAGENTA
        if status >= 500:
            return _RED + _BOLD
        if status >= 400:
            return _YELLOW
        if status >= 300:
            return _MAGENTA
        return _GREEN
    if key == "method":
        return _MAGENTA
    if key == "trace_id":
        return _DIM
    return _GREEN


def _color(value: str, color: str) -> str:
    return f"{color}{value}{_RESET}"


def _ansi_cell(value: str, width: int, color: str) -> str:
    clipped = _clip(value, width)
    padded = f"{clipped:<{width}}"
    return _color(padded, color)


def _clip(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 1:
        return value[:width]
    return value[: width - 1] + "…"


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    processors = _shared_processors()

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _renderer(debug),
        ],
        foreign_pre_chain=processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # 应用中间件已经输出带 trace_id 与耗时的标准 access log。
    # 关闭 uvicorn.access 可以避免同一次请求出现两行格式不一致的日志。
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").disabled = True
    for name in ("uvicorn", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(level)

    structlog.configure(
        processors=[*processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "xe6") -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
