"""
Defines custom response models used to serialize data.
"""

from typing import Any

import opentelemetry
import opentelemetry.trace
import orjson
from fastapi import responses


class ORJSONResponse(responses.ORJSONResponse):
    """Custom ORJSONResponse which includes the `OPT_SERIALIZE_NUMPY` option."""

    def render(self, content: Any) -> bytes:
        tracer = opentelemetry.trace.get_tracer(__name__)
        with tracer.start_as_current_span("orjson.dumps response"):
            return orjson.dumps(content, option=orjson.OPT_SERIALIZE_NUMPY)
