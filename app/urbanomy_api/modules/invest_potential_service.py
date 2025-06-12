import json
from typing import Dict, Any, List

from geojson_pydantic import FeatureCollection
from loguru import logger
from urbanomy.methods.investment_potential import LandUseScoreAnalyzer, LAND_USE_TO_POTENTIAL_COLUMN, \
    InvestmentAttractivenessAnalyzer
import pandas as pd
import geopandas as gpd
import math

from app.urbanomy_api.modules.urban_api_gateway import UrbanAPIGateway


class InvestmentPotentialService:
    @staticmethod
    async def calculate_landuse_score(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        analyzer = LandUseScoreAnalyzer(weights=None)
        score_gdf = analyzer.compute_scores_long(gdf)
        logger.info(f"landuse score have been calculated")
        return score_gdf

    @staticmethod
    async def get_territory_indicator_values(
            scenario_id: int,
            gdf: gpd.GeoDataFrame,
            as_long: bool = False,
    ) -> gpd.GeoDataFrame:
        """
        If as_long=False (default) — returns gdf with indicators as columns (wide).
        If as_long=True — returns GeoDataFrame with indicators as columns ['ip_type','ip_value','geometry'] (long).
        """
        indicators = await UrbanAPIGateway.get_indicator_values(scenario_id)
        attrs = {ind['indicator']['name_full']: ind['value'] for ind in indicators}
        for name, value in attrs.items():
            gdf[name] = value

        if not as_long:
            return gdf.to_crs(gdf.estimate_utm_crs())

        list_of_lists = gdf.apply(
            lambda row: [
                {
                    "ip_type": ip_type,
                    "ip_value": row[col],
                    "geometry": row.geometry
                }
                for ip_type, col in LAND_USE_TO_POTENTIAL_COLUMN.items()
            ],
            axis=1
        )

        records = [item for sublist in list_of_lists for item in sublist]

        if not records:
            return gpd.GeoDataFrame(
                columns=["ip_type", "ip_value", "geometry"],
                geometry="geometry",
                crs=gdf.crs
            )

        long_df = pd.DataFrame(records)
        long_gdf = gpd.GeoDataFrame(long_df, geometry="geometry", crs=gdf.crs)
        logger.info("Indicator values fetched successfully")
        return long_gdf.to_crs(long_gdf.estimate_utm_crs()).reset_index(drop=True)

    @staticmethod
    async def calculate_landuse_score_for_territory(
            gdf: gpd.GeoDataFrame,
            scenario_id: int
    ) -> gpd.GeoDataFrame | pd.DataFrame:
        indicators = await UrbanAPIGateway.get_indicator_values(scenario_id)
        indicator_attributes = {
            indicator['indicator']['name_full']: indicator['value']
            for indicator in indicators
        }

        for name, value in indicator_attributes.items():
            gdf[name] = value
        list_of_lists = gdf.apply(
            lambda row: [
                {
                    "ip_type": ip_type,
                    "ip_value": row[col_name],
                    "geometry": row.geometry
                }
                for ip_type, col_name in LAND_USE_TO_POTENTIAL_COLUMN.items()
            ],
            axis=1
        )
        records = [item for sublist in list_of_lists for item in sublist]
        long_df = pd.DataFrame(records)
        long_gdf = gpd.GeoDataFrame(long_df, geometry="geometry", crs=gdf.crs)
        long_gdf = long_gdf.to_crs(long_gdf.estimate_utm_crs())
        analyzer = LandUseScoreAnalyzer(weights=None)
        score_gdf = analyzer.compute_scores_long(long_gdf)

        return score_gdf

    @staticmethod
    async def calculate_investment_attractiveness(gdf: gpd.GeoDataFrame, benchmarks: dict[str, dict[str, any]]) \
            -> gpd.GeoDataFrame | pd.DataFrame:
        an = InvestmentAttractivenessAnalyzer(benchmarks=benchmarks)
        gdf_out, summary = an.calculate_investment_metrics(gdf)
        gdf_out["ECON_NPV"] = gdf_out["ECON_NPV"].astype(float)
        logger.info(f"Investment potential have been calculated")
        return gdf_out, summary

    @staticmethod
    async def map_zones(
            score_gdf: gpd.GeoDataFrame,
            zones_gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        # TODO update zone mapping when Max adds 'residetial' type

        ip_map: Dict[str, float] = score_gdf.set_index("ip_type")["ip_value"].to_dict()
        zone_map: Dict[str, int] = {
            "residential_individual": 10,
            "residential_lowrise": 11,
            "residential_midrise": 1,
            "residential_multistorey": 13,
            "business": 7,
            "recreation": 2,
            "special": 3,
            "industrial": 4,
            "agriculture": 5,
            "transport": 6
        }
        zone_to_ip = {v: k for k, v in zone_map.items()}

        residential_keys = [
            "residential_individual",
            "residential_lowrise",
            "residential_midrise",
            "residential_multistorey",
        ]
        max_res_val = max(ip_map[k] for k in residential_keys if k in ip_map)

        out = zones_gdf.copy()
        out = out.to_crs(out.estimate_utm_crs())
        out["ip_type"] = (
            out["zone_type_id"]
            .map(zone_to_ip)
            .fillna("residential_lowrise")
            .astype(str)
        )

        out['area'] = out.geometry.area

        def _resolve_value(zid: int, itype: str) -> float | None:
            if itype in residential_keys:
                return max_res_val
            return ip_map.get(itype)

        out["ip_value"] = out.apply(
            lambda row: _resolve_value(row["zone_type_id"], row["ip_type"]),
            axis=1
        )

        return out

    @staticmethod
    async def generate_response(
            gdf_out: gpd.GeoDataFrame,
            summary: pd.DataFrame,
            to_return: bool = False
    ) -> List[Dict[str, Any]]:
        if to_return == False:
            df = summary.rename_axis("land_use_type").reset_index()
            records = df.to_dict(orient="records")

            cleaned = []
            for rec in records:
                new_rec = {}
                for k, v in rec.items():
                    if isinstance(v, float) and math.isnan(v):
                        new_rec[k] = None
                    else:
                        new_rec[k] = v
                cleaned.append(new_rec)
            return cleaned

        if to_return == True:
            geojson_str = gdf_out.to_crs(4326).to_json()
            return json.loads(geojson_str)

    @staticmethod
    async def run_investment_calculation(scenario_id, as_geojson: bool, benchmarks: dict[str, dict[str, any]]) \
            -> gpd.GeoDataFrame | pd.DataFrame:
        logger.info(f"Running investment calculation for scenario {scenario_id}")
        territory_gdf = await UrbanAPIGateway.get_territory(scenario_id)
        territory_values_gdf = await InvestmentPotentialService.get_territory_indicator_values(scenario_id,
                                                                                               territory_gdf)
        landuse_score_gdf = await InvestmentPotentialService.calculate_landuse_score(territory_values_gdf)
        gdf_out, summary = await InvestmentPotentialService.calculate_investment_attractiveness(landuse_score_gdf,
                                                                                                benchmarks)
        response = await InvestmentPotentialService.generate_response(gdf_out, summary, as_geojson)
        return response

    @staticmethod
    async def run_investment_calculation_fzones(scenario_id, as_geojson: bool, benchmarks: dict[str, dict[str, any]]) \
            -> gpd.GeoDataFrame | pd.DataFrame:
        logger.info(f"Running investment calculation for scenario {scenario_id}")
        territory_gdf = await UrbanAPIGateway.get_territory(scenario_id)
        landuse_score_gdf = await InvestmentPotentialService.get_territory_indicator_values(scenario_id, territory_gdf,
                                                                                            as_long=True)
        functional_zones_gdf = await UrbanAPIGateway.get_functional_zones(scenario_id)
        mapped_zones_gdf = await InvestmentPotentialService.map_zones(landuse_score_gdf, functional_zones_gdf)
        mapped_zones_gdf = mapped_zones_gdf.to_crs(mapped_zones_gdf.estimate_utm_crs())
        gdf_out, summary = await InvestmentPotentialService.calculate_investment_attractiveness(
            mapped_zones_gdf,
            benchmarks)
        response = await InvestmentPotentialService.generate_response(gdf_out, summary, as_geojson)
        return response


    @staticmethod
    async def run_investment_calculation_coords(scenario_id, as_geojson: bool, benchmarks: dict[str, dict[str, any]],
                                                geojson: FeatureCollection) \
            -> gpd.GeoDataFrame | pd.DataFrame:
        gdf = gpd.GeoDataFrame.from_features(geojson)
        gdf = gdf.set_crs(4326)
        logger.info(f"Running investment calculation for scenario {scenario_id} and custom coords")
        territory_gdf = await UrbanAPIGateway.get_territory(scenario_id)
        landuse_score_gdf = await InvestmentPotentialService.get_territory_indicator_values(scenario_id, territory_gdf,
                                                                                            as_long=True)
        mapped_zones_gdf = await InvestmentPotentialService.map_zones(landuse_score_gdf, gdf)
        mapped_zones_gdf = mapped_zones_gdf.to_crs(mapped_zones_gdf.estimate_utm_crs())
        gdf_out, summary = await InvestmentPotentialService.calculate_investment_attractiveness(
            mapped_zones_gdf,
            benchmarks)
        response = await InvestmentPotentialService.generate_response(gdf_out, summary, as_geojson)
        return response
