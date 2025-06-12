from typing import Dict

from pydantic import BaseModel, Field

from geojson_pydantic.features import FeatureCollection

from app.urbanomy_api.dto.investment_attractivness_dto import ResidentialBenchmarkDto, NonResidentialBenchmarkDto, \
    residential_demo, non_residential_demo

class InvestmentAttractivenessCoordsDto(BaseModel):
    scenario_id: int = Field(..., example=198, description="Scenario ID")
    as_geojson: bool = Field(..., example=False, description="Which format to return")
    residential: Dict[str, ResidentialBenchmarkDto] = Field(
        default=residential_demo,
        description="Эталонные параметры для жилых категорий"
    )
    non_residential: Dict[str, NonResidentialBenchmarkDto] = Field(
        default=non_residential_demo,
        description="Эталонные параметры для остальных категорий"
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

