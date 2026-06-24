"""
OpenTelemetry setup for NewsFoundry backend.

- FastAPI HTTP spans       → OTel Collector → Jaeger
- Agent/tool/LLM spans    → OTel Collector → Phoenix  (via openinference tag)

openinference-instrumentation-openai-agents hooks into the openai-agents SDK
tracing system and emits spans with openinference.span.kind = AGENT | TOOL | LLM.
The OTel Collector routes these to Phoenix; HTTP spans go to Jaeger.
"""

import logging
import os

logger = logging.getLogger(__name__)


def setup_telemetry(app=None) -> bool:
    """Configure OTEL SDK and instrument FastAPI + OpenAI.

    Returns True if telemetry was successfully enabled.
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.info("[otel] OTEL_EXPORTER_OTLP_ENDPOINT not set — tracing disabled")
        return False

    auth_header = os.getenv("OTEL_EXPORTER_OTLP_AUTH_HEADER")

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": "newsfoundry-backend",
                "service.version": os.getenv("APP_VERSION", "0.0.0"),
                "deployment.environment": os.getenv("ENVIRONMENT", "production"),
                "openinference.project.name": "newsfoundry",
            }
        )

        headers = {"Authorization": auth_header} if auth_header else {}

        exporter = OTLPSpanExporter(
            endpoint=f"{endpoint}/v1/traces",
            headers=headers,
        )

        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        # Instrument outbound HTTP (httpx utilisé par openai SDK)
        HTTPXClientInstrumentor().instrument()

        # Instrument FastAPI
        if app is not None:
            FastAPIInstrumentor.instrument_app(app)

        # Instrument openai-agents SDK → agent/tool/LLM spans → Phoenix
        # Hooks into the agents SDK tracing system (not the raw openai SDK),
        # captures AgentSpan, FunctionSpan (tool calls), GenerationSpan (LLM).
        try:
            from openinference.instrumentation.openai_agents import (
                OpenAIAgentsInstrumentor,
            )

            OpenAIAgentsInstrumentor().instrument()
            logger.info("[otel] OpenAI Agents instrumentation enabled → Phoenix")
        except ImportError:
            logger.warning(
                "[otel] openinference-instrumentation-openai-agents not installed"
            )

        logger.info("[otel] Telemetry enabled → %s", endpoint)
        return True

    except Exception as e:
        logger.error("[otel] Failed to initialize telemetry: %s", e)
        return False
