from fastapi import Body
from pydantic import Field, BaseModel

from app.urbanomy_api.dto.benchmarks_dto import residential_demo, non_residential_demo, BenchmarksDto


class InvestmentAttractivenessFzonesRequestDto(BaseModel):
    scenario_id: int = Field(..., examples=[198], description="Scenario id")
    as_geojson: bool = Field(..., examples=[False], description="Which format to return")
    source: str = Field(None, description="The source of the landuse zones data. Valid options: PZZ, OSM, User"),
    benchmarks: BenchmarksDto = Body(
        default={**residential_demo, **non_residential_demo},
        description="Benchmark parameters for each functional zone category"
    )