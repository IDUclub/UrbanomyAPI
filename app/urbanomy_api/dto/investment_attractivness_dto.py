from fastapi import Body
from pydantic import BaseModel, Field

from app.urbanomy_api.dto.benchmarks_dto import BenchmarksDto


class InvestmentAttractivenessRequestDto(BaseModel):
    scenario_id: int = Field(..., example=198, description="Scenario id")
    as_geojson: bool = Field(..., example=False, description="Which format to return")
    benchmarks: BenchmarksDto = Body(
        ...,
        description="Benchmark parameters for each functional zone category"
    )
