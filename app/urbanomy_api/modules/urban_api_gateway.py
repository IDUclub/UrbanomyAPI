import geopandas as gpd
from loguru import logger

from app.common.exceptions.http_exception_wrapper import http_exception
from app.dependencies import urban_api_handler


class UrbanAPIGateway:
    SOURCE_PRIORITY = ["OSM", "PZZ", "User"]

    @staticmethod
    async def _form_source_params(sources: list[dict]) -> dict:
        max_year = max(s["year"] for s in sources)
        subset = [s for s in sources if s["year"] == max_year]

        for src in UrbanAPIGateway.SOURCE_PRIORITY:
            for s in subset:
                if s["source"] == src:
                    return s
        return subset[0]

    @staticmethod
    async def get_functional_zone_sources(
        scenario_id: int,
        source: str = None,
        token: str = None,
        year: int = None,
    ) -> dict:
        endpoint = f"/api/v1/scenarios/{scenario_id}/functional_zone_sources"
        response = await urban_api_handler.get(
            endpoint_url=endpoint, headers={"Authorization": f"Bearer {token}"}
        )
        if not response:
            raise http_exception(
                404, f"No functional zone sources found for scenario_id {scenario_id}"
            )

        if source and year is not None:
            matches = [
                s
                for s in response
                if s.get("source") == source and s.get("year") == year
            ]
            if not matches:
                raise http_exception(
                    404,
                    f"No functional zone source for source={source} and year={year}",
                )
            return matches[0]

        if source:
            subset = [s for s in response if s.get("source") == source]
            if not subset:
                raise http_exception(
                    404, f"No functional zone data for source={source}"
                )
            return max(subset, key=lambda s: s["year"])

        if year is not None:
            subset = [s for s in response if s.get("year") == year]
            if not subset:
                raise http_exception(404, f"No functional zone data for year={year}")
            return await UrbanAPIGateway._form_source_params(subset)

        return await UrbanAPIGateway._form_source_params(response)

    @staticmethod
    async def get_functional_zones(
        scenario_id: int,
        is_context: bool = False,
        source: str = None,
        token: str = None,
        year: int = None,
    ) -> gpd.GeoDataFrame:
        """
        Fetches functional zones for a project with an optional context flag and source selection.

        Parameters:
        project_id (int): ID of the project.
        is_context (bool): Flag to determine if context data should be fetched. Default is False.
        source (str, optional): The preferred source (PZZ or OSM). If not provided, the best source is selected automatically.

        Returns:
        dict: Response data from the API.

        Raises:
        http_exception: If the response is empty or the specified source is not available.
        """
        source_data = await UrbanAPIGateway.get_functional_zone_sources(
            scenario_id, source, token, year
        )

        if not source_data or "source" not in source_data or "year" not in source_data:
            raise http_exception(
                404, "No valid source found for the given scenario ID", scenario_id
            )

        source = source_data["source"]
        year = source_data["year"]

        endpoint = f"/api/v1/scenarios/{scenario_id}/functional_zones?year={year}&source={source}"

        response = await urban_api_handler.get(
            endpoint, headers={"Authorization": f"Bearer {token}" ""}
        )
        features = response.get("features", response)
        landuse_polygons = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

        if "properties" in landuse_polygons.columns:
            landuse_polygons["landuse_zone"] = landuse_polygons["properties"].apply(
                lambda x: x.get("landuse_zon") if isinstance(x, dict) else None
            )

        if "functional_zone_type" in landuse_polygons.columns:
            landuse_polygons["zone_type_id"] = landuse_polygons[
                "functional_zone_type"
            ].apply(lambda x: x.get("id") if isinstance(x, dict) else None)
            landuse_polygons["zone_type_name"] = landuse_polygons[
                "functional_zone_type"
            ].apply(
                lambda x: (
                    x.get("name")
                    if isinstance(x, dict) and x.get("name") != "unknown"
                    else "residential"
                )
            )

        landuse_polygons.drop(
            columns=[
                "properties",
                "functional_zone_type",
                "territory",
                "created_at",
                "updated_at",
                "zone_type_name",
                "functional_zone_id",
                "year",
                "source",
                "name",
            ],
            inplace=True,
            errors="ignore",
        )

        landuse_polygons.replace(
            {"landuse_zone": {None: "Residential"}, "zone_type_id": {14: 1}},
            inplace=True,
        )

        logger.info("Functional zones fetched")

        if not response or "features" not in response or not response["features"]:
            raise http_exception(
                404, "No functional zones found for the given scenario ID", scenario_id
            )

        return landuse_polygons

    @staticmethod
    async def get_project_id(scenario_id: int, token: str = None) -> int:
        endpoint = f"/api/v1/scenarios/{scenario_id}"
        response = await urban_api_handler.get(
            endpoint, headers={"Authorization": f"Bearer {token}" ""}
        )
        try:
            project_id = response.get("project", {}).get("project_id")
        except Exception:
            raise http_exception(
                404, "Project ID is missing in scenario data.", scenario_id
            )

        return project_id

    @staticmethod
    async def get_territory(scenario_id: int, token: str = None) -> gpd.GeoDataFrame:
        project_id = await UrbanAPIGateway.get_project_id(scenario_id, token)
        endpoint = f"/api/v1/projects/{project_id}/territory"
        try:
            response = await urban_api_handler.get(
                endpoint, headers={"Authorization": f"Bearer {token}" ""}
            )
        except Exception:
            raise http_exception(
                404, "No territory found for the given scenario ID", scenario_id
            )

        territory_geometry = response["geometry"]
        territory_feature = {
            "type": "Feature",
            "geometry": territory_geometry,
            "properties": {},
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([territory_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(polygon_gdf.estimate_utm_crs())
        logger.info(f"Territory have been loaded")
        return polygon_gdf

    @staticmethod
    async def get_indicator_values(scenario_id: int, token: str = None) -> dict:
        endpoint = f"/api/v1/scenarios/{scenario_id}/indicators_values"
        try:
            response = await urban_api_handler.get(
                endpoint, headers={"Authorization": f"Bearer {token}" ""}
            )
        except Exception:
            raise http_exception(
                404, "No indicators values found for the given scenario ID", scenario_id
            )
        return response


UrbanAPIGateway = UrbanAPIGateway()
