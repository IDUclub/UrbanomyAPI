import json
from typing import Dict, Any

from loguru import logger
from urbanomy.methods.investment_potential import LandUseScoreAnalyzer, LAND_USE_TO_POTENTIAL_COLUMN, \
    InvestmentAttractivenessAnalyzer
import pandas as pd
import geopandas as gpd
import math

from app.urbanomy_api.modules.urban_api_gateway import UrbanAPIGateway


class InvestmentPotentialService:
    @staticmethod
    async def calculate_landuse_score(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame | pd.DataFrame:
        analyzer = LandUseScoreAnalyzer(weights=None)
        score_gdf = analyzer.compute_scores_long(gdf)
        return score_gdf

    @staticmethod
    async def get_territory_indicator_values(
            scenario_id: int,
            gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        indicators = await UrbanAPIGateway.get_indicator_values(scenario_id)
        indicator_attributes = {
            ind['indicator']['name_full']: ind['value']
            for ind in indicators
        }

        for name, value in indicator_attributes.items():
            gdf[name] = value

        records = []
        for _, row in gdf.iterrows():
            for ip_type, col_name in LAND_USE_TO_POTENTIAL_COLUMN.items():
                records.append({
                    "ip_type": ip_type,
                    "ip_value": row[col_name],
                    "geometry": row.geometry
                })

        if not records:
            return gpd.GeoDataFrame(columns=["ip_type", "ip_value", "geometry"],
                                    geometry="geometry",
                                    crs=gdf.crs)

        rec_df = pd.DataFrame(records)
        result = gpd.GeoDataFrame(
            rec_df,
            geometry="geometry",
            crs=gdf.crs
        )

        result = result.to_crs(result.estimate_utm_crs())
        result = result.reset_index(drop=True)
        return result

    @staticmethod
    async def calculate_investment_attractiveness(gdf: gpd.GeoDataFrame, benchmarks: dict[str, dict[str, any]]) \
            -> gpd.GeoDataFrame | pd.DataFrame:
        an = InvestmentAttractivenessAnalyzer(benchmarks=benchmarks)
        gdf_out, summary = an.calculate_investment_metrics(gdf)
        gdf_out["ECON_NPV"] = gdf_out["ECON_NPV"].astype(float)
        return gdf_out, summary

    @staticmethod
    async def map_zones(
            score_gdf: gpd.GeoDataFrame,
            zones_gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:

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
    async def run_investment_calculation(scenario_id, to_return: str, benchmarks: dict[str, dict[str, any]]) \
            -> gpd.GeoDataFrame | pd.DataFrame:
        logger.info(f"Running investment calculation for scenario {scenario_id}")
        territory_gdf = await UrbanAPIGateway.get_territory(scenario_id)
        logger.info(f"Territory have been loaded")
        landuse_score_gdf = await InvestmentPotentialService.calculate_landuse_score(territory_gdf, scenario_id)
        logger.info(f"landuse score have been calculated")
        gdf_out, summary = await InvestmentPotentialService.calculate_investment_attractiveness(landuse_score_gdf,
                                                                                                benchmarks)
        logger.info(f"Investment potential have been calculated")

        if to_return == "dataframe":
            records = summary.to_dict(orient="records")
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

        if to_return == "geodataframe":
            gdf = gdf_out.copy()
            gdf = gdf.to_crs(4236)
            geom = gdf.geometry.iloc[0]
            geom_geojson = geom.__geo_interface__
            props_cols = [c for c in gdf.columns if c not in ("geometry", "ip_type")]

            properties: Dict[str, Dict[str, Any]] = {}
            for _, row in gdf.iterrows():
                key = row["ip_type"]
                nested: dict = {}
                for c in props_cols:
                    val = row[c]
                    if pd.isna(val):
                        nested[c] = None
                    else:
                        nested[c] = val
                properties[key] = nested

            feature = {
                "type": "Feature",
                "geometry": geom_geojson,
                "properties": properties
            }
            return feature

    @staticmethod
    async def run_investment_calculation_fzones(scenario_id, to_return: str, benchmarks: dict[str, dict[str, any]]) \
        -> gpd.GeoDataFrame | pd.DataFrame:
        logger.info(f"Running investment calculation for scenario {scenario_id}")
        territory_gdf = await UrbanAPIGateway.get_territory(scenario_id)
        landuse_score_gdf = await InvestmentPotentialService.get_territory_indicator_values(scenario_id, territory_gdf)
        logger.info(f"Territory have been loaded")
        logger.info(f"landuse score have been calculated")
        functional_zones_gdf = await UrbanAPIGateway.get_functional_zones(scenario_id)
        mapped_zones_gdf = await InvestmentPotentialService.map_zones(landuse_score_gdf,functional_zones_gdf)
        mapped_zones_gdf = mapped_zones_gdf.to_crs(mapped_zones_gdf.estimate_utm_crs())
        gdf_out, summary = await InvestmentPotentialService.calculate_investment_attractiveness(mapped_zones_gdf,
                                                                                                benchmarks)
        logger.info(f"Investment potential have been calculated")

        if to_return == "dataframe":
            records = summary.to_dict(orient="records")
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

        if to_return == "geodataframe":
            geojson_str = gdf_out.to_crs(4326).to_json()
            return json.loads(geojson_str)



