from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse
from loguru import logger

from app.common.middlewares.prometheus_handler import ObservabilityMiddleware
from app.logs_router.logs_controller import logs_router

from .dependencies import config
from .observability import OpenTelemetryAgent, PrometheusConfig
from .observability.metrics import setup_metrics
from .urbanomy_api.urbanomic_controller import urbanomic_router


def _get_prometheus_port() -> int:
    try:
        return int(config.get("PROMETHEUS_PORT"))
    except ValueError:
        return 9464


metrics = setup_metrics()


@asynccontextmanager
async def lifespan(app: FastAPI):
    prometheus_port = _get_prometheus_port()
    otel_agent = OpenTelemetryAgent(
        prometheus_config=PrometheusConfig(
            host="0.0.0.0",
            port=prometheus_port,
        ),
    )
    logger.info(f"Prometheus server started on {prometheus_port}")
    yield
    otel_agent.shutdown()
    logger.info("Prometheus server was shut down")


app = FastAPI(
    title="Urbanomy API",
    description="API for calculating investing attractiveness of territory using Urbanomy library",
    version=config.get("APP_VERSION"),
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=100)
app.add_middleware(ObservabilityMiddleware, metrics=metrics)


@app.get("/", include_in_schema=False)
async def read_root():
    return RedirectResponse("/docs")


app.include_router(urbanomic_router)
app.include_router(logs_router)
