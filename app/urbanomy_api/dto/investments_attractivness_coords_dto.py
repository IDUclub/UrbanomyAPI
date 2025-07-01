from fastapi import Body
from pydantic import BaseModel, Field

from app.urbanomy_api.dto.benchmarks_dto import (BenchmarksDTO,
                                                 non_residential_demo,
                                                 residential_demo)
from app.urbanomy_api.schemas.features_model import (EXAMPLE_GEOMETRY,
                                                     FeatureCollection)


class InvestmentAttractivenessCoordsDto(BaseModel):
    scenario_id: int = Field(..., examples=[198], description="Scenario id")
    as_geojson: bool = Field(
        ..., examples=[False], description="Which format to return"
    )
    benchmarks: BenchmarksDTO = Body(
        default={**residential_demo, **non_residential_demo},
        description="Benchmark parameters for each functional zone category",
    )

    geometry: FeatureCollection = Body(
        ...,
        description="GeoJSON FeatureCollection with geometries and zone_type_id property",
        examples=[
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "id": 42,
                        "geometry": EXAMPLE_GEOMETRY,
                        "properties": {"zone_type_id": 1},
                    }
                ],
            }
        ],
    )
