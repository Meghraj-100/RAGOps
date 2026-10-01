"""OpenTelemetry tracing setup."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from app.core.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()

_tracer: trace.Tracer | None = None


def setup_tracing():
    """Initialize OpenTelemetry tracing with OTLP exporter."""
    if not settings.otel_enabled:
        logger.info("otel_tracing_disabled")
        return

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)

    try:
        insecure = not settings.otel_exporter_otlp_endpoint.startswith("https")
        headers = None
        if settings.otel_exporter_otlp_headers:
            headers = dict(item.split("=") for item in settings.otel_exporter_otlp_headers.split(","))

        exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=insecure,
            headers=headers
        )
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        logger.info("otel_tracing_configured", endpoint=settings.otel_exporter_otlp_endpoint, insecure=insecure)
    except Exception as e:
        logger.warning("otel_tracing_setup_failed", error=str(e))

    trace.set_tracer_provider(provider)


def get_tracer() -> trace.Tracer:
    """Get the application tracer."""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(settings.otel_service_name)
    return _tracer
