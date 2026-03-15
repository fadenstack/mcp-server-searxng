"""Logging configuration — loguru + OpenTelemetry trace enrichment."""

from __future__ import annotations

import logging
import sys

from loguru import logger

from mcp_server.settings import settings


class InterceptHandler(logging.Handler):
    """Route stdlib logging records into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame, depth = logging.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _record_formatter(record: dict) -> str:
    """Append OpenTelemetry trace/span IDs when available."""
    trace_id = span_id = "0"
    try:
        from opentelemetry import trace as otrace

        ctx = otrace.get_current_span().get_span_context()
        if ctx and ctx.trace_id:
            trace_id = format(ctx.trace_id, "032x")
            span_id = format(ctx.span_id, "016x")
    except ImportError:
        pass

    record["extra"]["trace_id"] = trace_id
    record["extra"]["span_id"] = span_id

    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<magenta>trace_id={extra[trace_id]}</magenta> | "
        "<blue>span_id={extra[span_id]}</blue> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>\n"
    )


def configure_logging() -> None:
    """Wire up loguru as the sole log handler."""
    logger.remove()
    logger.add(
        sys.stderr,
        format=_record_formatter,
        level=settings.log_level.upper(),
        enqueue=True,
    )

    intercept = InterceptHandler()
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "httpx"):
        target = logging.getLogger(name)
        target.handlers = [intercept]
        target.propagate = False
