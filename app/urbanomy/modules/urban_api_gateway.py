import geopandas as gpd
import pandas as pd

from app.dependencies import urban_api_handler, http_exception


class UrbanAPIGateway:
    @staticmethod
    async def _form_source_params(sources: list[dict]) -> dict:
        if len(sources) == 1:
            return sources[0]

        source_names = [item["source"] for item in sources]
        df_sources = pd.DataFrame(sources)

        if "OSM" in source_names:
            idx = df_sources[df_sources["source"] == "OSM"]["year"].idxmax()
            return df_sources.loc[idx].to_dict()

        if "PZZ" in source_names:
            idx = df_sources[df_sources["source"] == "PZZ"]["year"].idxmax()
            return df_sources.loc[idx].to_dict()

        idx = df_sources[df_sources["source"] == "User"]["year"].idxmax()
        return df_sources.loc[idx].to_dict()

    async def get_functional_zone_sources(
        self,
        scenario_id: int,
        source: str = None
    ) -> dict:

        endpoint = f"/api/v1/scenarios/{scenario_id}/functional_zone_sources"
        response = await urban_api_handler.get(endpoint_url=endpoint)

        if not response:
            raise http_exception(404, f"No functional zone sources found for scenario_id", scenario_id)

        if source:
            source_data = next((s for s in response if s.get("source") == source), None)
            if not source_data:
                raise http_exception(404, f"No data found for the specified source", source)
            return source_data

        best = await self._form_source_params(response)
        return best

    @staticmethod
    async def get_functional_zones(scenario_id: int, is_context: bool = False, source: str = None) -> dict:
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
        source_data = await UrbanAPIGateway.get_functional_zone_sources(scenario_id, source)

        if not source_data or "source" not in source_data or "year" not in source_data:
            raise http_exception(404, "No valid source found for the given scenario ID", scenario_id)

        source = source_data["source"]
        year = source_data["year"]

        endpoint = (f"/api/v1/scenarios/{scenario_id}/functional_zones?year={year}&source={source}"
                    )

        response = await urban_api_handler.get(endpoint)
        if not response or "features" not in response or not response["features"]:
            raise http_exception(404, "No functional zones found for the given scenario ID", scenario_id)

        return response

    @staticmethod
    async def get_project_id(scenario_id: int) -> int:
        endpoint = f"api/v1/scenarios/{scenario_id}"
        response = await urban_api_handler.get(endpoint)
        try:
            project_id = response.get("project", {}).get("project_id")
        except Exception:
            raise http_exception(404, "Project ID is missing in scenario data.", scenario_id)

        return project_id

    @staticmethod
    async def get_territory(scenario_id: int) -> gpd.GeoDataFrame:
        project_id = UrbanAPIGateway.get_project_id(scenario_id)
        endpoint = f"api/v1/projects/{project_id}/territory"
        try:
            response = await urban_api_handler.get(endpoint)
        except Exception:
            raise http_exception(404, "No territory found for the given scenario ID", scenario_id)

        territory_geometry = response["geometry"]
        territory_feature = {
            'type': 'Feature',
            'geometry': territory_geometry,
            'properties': {}
        }
        polygon_gdf = gpd.GeoDataFrame.from_features([territory_feature], crs=4326)
        polygon_gdf = polygon_gdf.to_crs(polygon_gdf.estimate_utm_crs())
        return polygon_gdf

    @staticmethod
    async def get_indicator_values(scenario_id: int, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        endpoint = f"api/v1/scenarios/{scenario_id}/indicators_values"
        try:
            response = await urban_api_handler.get(endpoint)
        except Exception:
            raise http_exception(404, "No indicators values found for the given scenario ID", scenario_id)

        indicator_attributes = {
            indicator['indicator']['name_full']: indicator['value']
            for indicator in response
        }

        for name, value in indicator_attributes.items():
            gdf[name] = value

        return gdf


UrbanAPIGateway = UrbanAPIGateway()

