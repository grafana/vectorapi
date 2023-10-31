"""main.py is the entrypoint of the gateway."""
import os
from contextlib import asynccontextmanager

import fastapi
import loguru
import uvicorn
import uvloop
from fastapi_route_logger_middleware import RouteLoggerMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from starlette.responses import Response
from starlette_exporter import PrometheusMiddleware, handle_metrics

from vectorapi import log, responses
from vectorapi.docs import OPENAPI_DESCRIPTION, OPENAPI_TAGS_METADATA
from vectorapi.pgvector.base import Base
from vectorapi.pgvector.db import engine
from vectorapi.routes.collection_points import router as collection_points_router
from vectorapi.routes.collections import router as collections_router
from vectorapi.routes.embeddings import router as embeddings_routers

# The app name, used in tracing span attributes and Prometheus metric names/labels.
APP_NAME = "vectorapi"
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")


def initialize_tracing() -> None:
    set_global_textmap(JaegerPropagator())
    tracer_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: APP_NAME}))
    trace.set_tracer_provider(tracer_provider)
    otlp_exporter = OTLPSpanExporter()

    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    AsyncPGInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()


async def health(request: fastapi.Request):
    """
    Check if this service is healthy, if there are too many threadpool threads in use
    there is a risk of high latency and the service should be marked as
    unhealthy.
    """
    return Response("OK", status_code=fastapi.status.HTTP_200_OK)


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    # executed before the application starts taking requests

    # sync the schema so we know which tables exist on boot
    loguru.logger.debug("Syncing postgres schema metadata..")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.reflect)
    yield

    # executed after the application finishes handling requests


def create_app() -> fastapi.FastAPI:
    """create_app instantiates the FastAPI app."""
    loguru.logger.debug("Setting up FastAPI app..")
    if OTEL_EXPORTER_OTLP_ENDPOINT:
        initialize_tracing()

    app = fastapi.FastAPI(
        title="VectorAPI",
        description=OPENAPI_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS_METADATA,
        default_response_class=responses.ORJSONResponse,
        lifespan=lifespan,
    )
    logger = loguru.logger.patch(log.add_trace_id)
    app.add_middleware(RouteLoggerMiddleware, logger=logger)
    app.add_middleware(
        PrometheusMiddleware,
        app_name=APP_NAME,
        prefix=APP_NAME,
        group_paths=True,
        buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
    )
    app.add_route("/metrics", handle_metrics)
    app.add_route("/healthz", health)
    log.init_logging()
    app.include_router(embeddings_routers, prefix="/v1")
    app.include_router(collections_router, prefix="/v1")
    app.include_router(collection_points_router, prefix="/v1")
    FastAPIInstrumentor.instrument_app(app)
    return app


uvloop.install()
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8889)),
        log_level="debug",
    )
