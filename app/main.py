import aiofiles
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .dependencies import config
from .urbanomy.urbanomic_controller import urbanomic_router

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


@app.get("/", response_model=dict[str, str])
def read_root():
    return RedirectResponse(url='/docs')


@app.get("/status")
async def read_root():
    return {"status": "OK"}


@app.get("/logs")
async def read_logs():
    async with aiofiles.open(config.get("LOGS_FILE")) as logs_file:
        logs = await logs_file.read()
        return logs[-1:-10000]


app.include_router(urbanomic_router)
