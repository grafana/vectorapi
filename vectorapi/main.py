"""main.py is the entrypoint of the gateway."""
import os
from contextlib import asynccontextmanager

import fastapi
import loguru
import uvloop
from fastapi_route_logger_middleware import RouteLoggerMiddleware
from opentelemetry import trace
from opentelemetry.exporter.jaeger import thrift
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from starlette.responses import Response
from starlette_exporter import PrometheusMiddleware, handle_metrics

from vectorapi import log, responses
from vectorapi.routes.collection_points import router as collection_points_router
from vectorapi.routes.collections import router as collections_router
from vectorapi.routes.embeddings import router as embeddings_routers
from vectorapi.stores.store_client import client

# The app name, used in tracing span attributes and Prometheus metric names/labels.
APP_NAME = "vectorapi"
JAEGER_HOST = os.getenv("JAEGER_HOST")


def initialize_tracing() -> None:
    """initialize_tracing configures the OpenTelemetry Jaeger exporter."""
    set_global_textmap(JaegerPropagator())
    tracer_provider = TracerProvider(resource=Resource.create({SERVICE_NAME: APP_NAME}))
    trace.set_tracer_provider(tracer_provider)
    jaeger_exporter = thrift.JaegerExporter()

    tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))


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
    await client.setup()
    yield

    # executed after the application finishes handling requests
    await client.teardown()


def create_app() -> fastapi.FastAPI:
    """create_app instantiates the FastAPI app."""
    if JAEGER_HOST:
        initialize_tracing()

    app = fastapi.FastAPI(default_response_class=responses.ORJSONResponse, lifespan=lifespan)
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
