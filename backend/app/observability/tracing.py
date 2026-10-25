from opentelemetry import trace
from app.core.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()

_tracer: trace.Tracer | None = None


def setup_tracing():
    """Initialize OpenTelemetry tracing with OTLP exporter if available."""
    if not settings.otel_enabled:
        logger.info("otel_tracing_disabled")
        return

    try:
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)

        insecure = not settings.otel_exporter_otlp_endpoint.startswith("https")
        headers = None
        if settings.otel_exporter_otlp_headers:
            headers = {}
            for item in settings.otel_exporter_otlp_headers.split(","):
                if "=" in item:
                    k, v = item.split("=", 1)
                    headers[k.strip()] = v.strip()

        exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=insecure,
            headers=headers if headers else None,
        )
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        logger.info("otel_tracing_configured", endpoint=settings.otel_exporter_otlp_endpoint, insecure=insecure)
    except Exception as e:
        logger.warning("otel_tracing_setup_failed", error=str(e))



def get_tracer() -> trace.Tracer:
    """Get the application tracer."""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(settings.otel_service_name)
    return _tracer
