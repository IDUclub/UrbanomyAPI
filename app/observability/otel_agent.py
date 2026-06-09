"""Open Telemetry agent initialization is defined here"""

import platform
from functools import cache

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import (
    SERVICE_INSTANCE_ID,
    SERVICE_NAME,
    SERVICE_VERSION,
    Resource,
)
from loguru import logger

from app.dependencies import config

from .config import PrometheusConfig
from .metrics_server import PrometheusServer


@cache
def get_resource() -> Resource:
    return Resource.create(
        attributes={
            SERVICE_NAME: "urbanomy-api",
            SERVICE_VERSION: config.get("APP_VERSION"),
            SERVICE_INSTANCE_ID: platform.node(),
        }
    )


class OpenTelemetryAgent:  # pylint: disable=too-few-public-methods
    def __init__(
        self,
        prometheus_config: PrometheusConfig | None,
    ):
        self._resource = get_resource()
        self._prometheus: PrometheusServer | None = None

        if prometheus_config is not None:
            try:
                self._prometheus = PrometheusServer(
                    port=prometheus_config.port, host=prometheus_config.host
                )
            except OSError as exc:
                # Another worker already bound the metrics port (gunicorn multi-worker).
                # Skip serving metrics from this worker instead of crashing it.
                self._prometheus = None
                logger.warning(
                    f"Prometheus server not started on {prometheus_config.port}: {exc}"
                )
                return

            reader = PrometheusMetricReader()
            provider = MeterProvider(resource=self._resource, metric_readers=[reader])
            metrics.set_meter_provider(provider)

    def shutdown(self) -> None:
        """Stop metrics and tracing services if they were started."""
        if self._prometheus is not None:
            self._prometheus.shutdown()
