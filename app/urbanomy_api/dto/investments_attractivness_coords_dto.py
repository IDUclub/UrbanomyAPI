from typing import Any, Dict

from pydantic import BaseModel, Field

from app.urbanomy_api.dto.investment_attractivness_dto import benchmarks_demo
from geojson_pydantic.features import FeatureCollection


class InvestmentAttractivenessCoordsDto(BaseModel):
    scenario_id: int = Field(..., example=198, description="Scenario ID")
    to_return: str = Field(..., example="geodataframe", description="Which format to return")


class InvestmentAttractivenessCoordsBody(BaseModel):
    benchmarks: Dict[str, Dict[str, Any]] = Field(
        ...,
        example=benchmarks_demo,
        description="Dictionary of benchmarks data for each land use category"
    )
    geometry: FeatureCollection = Field(
        ...,
        description="GeoJSON FeatureCollection with geometry data",
        example={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [31.0406076, 59.9224151],
                                [31.0392415, 59.9217319],
                                [31.0423422, 59.9204629],
                                [31.0416663, 59.9200381],
                                [31.0379064, 59.9216766],
                                [31.0384506, 59.9236044],
                                [31.0406076, 59.9224151]
                            ]
                        ]
                    },
                    "properties": {
                        "zone_type_id": 1
                    }
                }
            ]
        }
    )
