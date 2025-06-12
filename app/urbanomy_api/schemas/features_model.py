from typing import Any, Optional, Self
from pydantic import BaseModel, Field, model_validator
from typing import Literal, List, Dict
import shapely
import shapely.geometry as geom
import json

EXAMPLE_GEOMETRY: Dict[str, Any] = {
    "type": "Polygon",
    "coordinates": [
        [
            [31.038556, 59.922080],
            [31.036947, 59.920413],
            [31.040023, 59.919382],
            [31.041870, 59.920945],
            [31.038556, 59.922080]
        ]
    ]
}


class Geometry(BaseModel):
    """
    Geometry representation for GeoJSON model.
    """
    type: Literal["Polygon", "MultiPolygon"] = Field(
        ...,
        examples=[EXAMPLE_GEOMETRY["type"]]
    )
    coordinates: List[Any] = Field(
        ...,
        description="list[list[list[float]]] for Polygon",
        examples=[EXAMPLE_GEOMETRY["coordinates"]]
    )

    _shapely_geom: Optional[geom.Polygon | geom.MultiPolygon] = None

    def as_shapely_geometry(
            self,
    ) -> geom.Polygon | geom.MultiPolygon | geom.LineString:
        """
        Return Shapely geometry object from the parsed geometry.
        """
        if self._shapely_geom is None:
            geojson = {"type": self.type, "coordinates": self.coordinates}
            self._shapely_geom = shapely.from_geojson(json.dumps(geojson))
        return self._shapely_geom

    @classmethod
    def from_shapely_geometry(
            cls, geometry: geom.Polygon | geom.MultiPolygon | None
    ) -> Optional["Geometry"]:
        """
        Construct Geometry model from shapely geometry.
        """
        if geometry is None:
            return None
        return cls(**geom.mapping(geometry))


class PolygonalGeometry(BaseModel):
    """
    Geometry representation for Polygon/MultiPolygon as dict
    """
    type: Literal["Polygon", "MultiPolygon"] = Field(
        ...,
        examples=[EXAMPLE_GEOMETRY["type"]]
    )
    coordinates: List[Any] = Field(
        ...,
        description="list[list[list[float]]] for Polygon",
        examples=[EXAMPLE_GEOMETRY["coordinates"]]
    )

    @model_validator(mode="after")
    def validate_geom(self) -> Self:
        """
        Validating that the geometry dict is valid
        """
        # count nesting depth
        depth = 0
        ref = self.coordinates
        while isinstance(ref, list):
            ref = ref[0]
            depth += 1

        if depth not in (3, 4):
            raise ValueError(f"Invalid Polygon/MultiPolygon nesting depth: {depth}")

        return self

    def as_dict(self) -> dict:
        return {"type": self.type, "coordinates": self.coordinates}


class Feature(BaseModel):
    type: Literal["Feature"] = Field(
        ...,
        examples=["Feature"]
    )
    id: Optional[int] = Field(
        default=None,
        examples=[7]
    )
    geometry: PolygonalGeometry
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        examples=[{"zone_type_id": 5}]
    )

    def as_dict(self) -> dict:
        return {
            "type": "Feature",
            "id": self.id,
            "geometry": self.geometry.as_dict(),
            "properties": self.properties
        }


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = Field(
        ...,
        examples=["FeatureCollection"]
    )
    features: List[Feature] = Field(
        ...,
        description="Список геометрий с их свойствами"
    )

    def as_geo_dict(self) -> dict:
        return {
            "type": "FeatureCollection",
            "features": [f.as_dict() for f in self.features]
        }
