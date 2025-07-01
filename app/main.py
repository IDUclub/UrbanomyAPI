from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse

from app.logs_router.logs_controller import logs_router

from .dependencies import config
from .urbanomy_api.urbanomic_controller import urbanomic_router


app = FastAPI(
    title="Urbanomy API",
    description="API for calculating investing attractiveness of territory using Urbanomy library",
    version=config.get("APP_VERSION"),
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


@app.get("/", include_in_schema=False)
async def read_root():
    return RedirectResponse("/docs")


app.include_router(urbanomic_router)
app.include_router(logs_router)
