from enum import Enum

from fastapi import Body
from pydantic import Field, BaseModel

from app.urbanomy_api.dto.benchmarks_dto import residential_demo, non_residential_demo, BenchmarksDTO


class Source(str, Enum):
    PZZ = "PZZ"
    OSM = "OSM"
    User = "User"


class InvestmentAttractivenessFunctionalZonesRequestDTO(BaseModel):
    scenario_id: int = Field(..., examples=[198], description="Scenario id")
    as_geojson: bool = Field(..., examples=[False], description="Which format to return")
    source: Source = Field(
        ...,
        description="The source of the landuse zones data. Valid options: PZZ, OSM, User"
    )
    benchmarks: BenchmarksDTO = Body(
        default={**residential_demo, **non_residential_demo},
        description="Benchmark parameters for each functional zone category"
    )
