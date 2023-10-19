"""Configure handlers and formats for application loggers."""
from __future__ import annotations

import inspect
import logging
import sys
from pprint import pformat

import loguru
from loguru import logger
from loguru._defaults import LOGURU_FORMAT
from opentelemetry.trace import get_current_span
from opentelemetry.trace.span import format_trace_id


def _get_log_level(record: logging.LogRecord) -> int | str:
    # Get corresponding Loguru level for a log record, if it exists.
    try:
        return logger.level(record.levelname).name
    except ValueError:
        if record.levelno == 5:
            return "TRACE"
        return record.levelno


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentaion.
    See https://loguru.readthedocs.io/en/stable/overview.html
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class OpenTelemetryPropagateHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        sp = get_current_span()
        if sp is None:
            return
        level = _get_log_level(record)

        # Truncate the message so that extremely long log lines (e.g. DataFrames)
        # don't get sent to OpenTelemetry.
        message = record.getMessage()[:200]

        # It feels like the 'name' of the span should be the name of the logger,
        # and the message should be recorded under the 'message' attribute.
        # However, it looks like the Jaeger exporter exports the 'name' under
        # the 'message' key, so doing it this way works better.
        # Source:
        # https://github.com/open-telemetry/opentelemetry-python/blob/6f8c077fa5349d445358b879fc83c139a0c22cff/exporter/opentelemetry-exporter-jaeger-thrift/src/opentelemetry/exporter/jaeger/thrift/translate/__init__.py#L272-L278
        sp.add_event(message, {"name": record.name, "level": level})


def format_record(record: loguru.Record) -> str:
    """
    Custom format for loguru loggers.
    Uses pformat for log any data like request/response body during debug.
    Works with logging if loguru handler it.
    Example:
    >>> payload = [{"users":[
    ...     {"name": "Nick", "age": 87, "is_active": True},
    ...     {"name": "Alex", "age": 27, "is_active": True},
    ... ], "count": 2}]
    >>> logger.bind(payload=payload).debug("users payload")
    >>> [   {   'count': 2,
    ...         'users': [   {'age': 87, 'is_active': True, 'name': 'Nick'},
    ...                      {'age': 27, 'is_active': True, 'name': 'Alex'}]}]
    """
    format_string: str = LOGURU_FORMAT

    if record["extra"].get("task_id") is not None:
        format_string += " | <level>task_id={extra[task_id]}</level>"

    if record["extra"].get("task_name") is not None:
        format_string += " | <level>task_name={extra[task_name]}</level>"

    if record["extra"].get("trace_id") is not None:
        format_string += " | <level>trace_id={extra[trace_id]}</level>"

    if record["extra"].get("training_id") is not None:
        format_string += " | <level>training_id={extra[training_id]}</level> "

    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(
            record["extra"]["payload"], indent=4, compact=True, width=88
        )
        format_string += "\n<level>{extra[payload]}</level>"

    format_string += "{exception}\n"
    return format_string


def add_trace_id(record: loguru.Record) -> None:
    sp = get_current_span()
    if sp is None:
        return

    trace_id = sp.get_span_context().trace_id
    record["extra"].update(trace_id=format_trace_id(trace_id))


def patch_logger(record: loguru.Record):
    add_trace_id(record)


def intercept_handler(module_name: str):
    """
    Intercept handler for specific module.
    """
    # disable handlers for specific module to avoid duplicate logs
    sub_loggers = (
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if name.startswith(f"{module_name}.")
    )
    for sub_logger in sub_loggers:
        sub_logger.handlers = []

    # redirect output of module logger to loguru
    logging.getLogger(module_name).handlers = [InterceptHandler()]


def init_logging():
    """
    Replaces logging handlers with a handler for using the custom handler.
    """

    # disable handlers for specific uvicorn loggers
    intercept_handler("uvicorn")
    intercept_handler("sqlalchemy")

    # set logs output, level and format
    logger.configure(
        handlers=[{"sink": sys.stdout, "format": format_record}],
        patcher=patch_logger,
    )
    logger.add(OpenTelemetryPropagateHandler(), format="{message}")
