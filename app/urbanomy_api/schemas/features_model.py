from typing import Any, Optional
from typing_extensions import Self
from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Literal, List, Dict
import shapely
import shapely.geometry as geom
import json

from app.common.exceptions.http_exception_wrapper import http_exception

EXAMPLE_GEOMETRY: Dict[str, Any] = {
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
        examples=[{"zone_type_id": 1}]
    )

    def as_dict(self) -> dict:
        return {
            "type": "Feature",
            "id": self.id,
            "geometry": self.geometry.as_dict(),
            "properties": self.properties
        }

    @field_validator("properties", mode="after")
    @classmethod
    def must_have_zone_type_id(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if "zone_type_id" not in v:
            raise http_exception(422, "each Feature.properties must include a 'zone_type_id'")
        if not isinstance(v["zone_type_id"], int):
            raise http_exception(422, "'zone_type_id' must be an integer")
        return v


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = Field(
        ...,
        examples=["FeatureCollection"]
    )
    features: List[Feature] = Field(
        ...,
        description="Geometries with feature properties"
    )

    def as_geo_dict(self) -> dict:
        return {
            "type": "FeatureCollection",
            "features": [f.as_dict() for f in self.features]
        }
