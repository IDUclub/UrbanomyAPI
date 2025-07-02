import json
import math
from typing import Any, Dict, List

import geopandas as gpd
import pandas as pd
from loguru import logger
from urbanomy.methods.investment_potential import (
    LAND_USE_TO_POTENTIAL_COLUMN, InvestmentAttractivenessAnalyzer,
    LandUseScoreAnalyzer)

from app.common.exceptions.http_exception_wrapper import http_exception
from app.urbanomy_api.constants.zone_mapping import zone_mapping
from app.urbanomy_api.modules.urban_api_gateway import UrbanAPIGateway
from app.urbanomy_api.schemas.features_model import FeatureCollection


class InvestmentPotentialService:
    @staticmethod
    async def calculate_landuse_score(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        try:
            analyzer = LandUseScoreAnalyzer(weights=None)
            score_gdf = analyzer.compute_scores_long(gdf)
            logger.info(f"landuse score have been calculated")
        except Exception as e:
            logger.exception("Error occurred while calculating landuse score")
            raise http_exception(
                status_code=500,
                msg="Error calculating landuse score",
                _input=gdf,
                _detail={"error": str(e)},
            )
        return score_gdf

    @staticmethod
    def _required_columns(benchmarks: dict[str, dict[str, any]]) -> set[str]:
        """Translate land-use keys in `benchmarks` into indicator column names."""
        return {
            LAND_USE_TO_POTENTIAL_COLUMN[key]
            for key, val in benchmarks.items()
            if val is not None and key in LAND_USE_TO_POTENTIAL_COLUMN
        }

    @staticmethod
    async def get_territory_indicator_values(
        scenario_id: int,
        gdf: gpd.GeoDataFrame,
        benchmarks: dict[str, dict[str, any]],
        as_long: bool = False,
        token: str | None = None,
    ) -> gpd.GeoDataFrame:
        """
        If as_long=False (default) — returns gdf with indicators as columns (wide).
        If as_long=True — returns GeoDataFrame with indicators as columns ['ip_type','ip_value','geometry'] (long).
        """

        indicators = await UrbanAPIGateway.get_indicator_values(
            scenario_id, token=token
        )
        attrs = {ind["indicator"]["name_full"]: ind["value"] for ind in indicators}
        for name, value in attrs.items():
            gdf[name] = value
        requested_keys = [k for k, v in benchmarks.items() if v is not None]

        res_cols_detailed = [
            "Потенциал развития среднеэтажной жилой застройки",
            "Потенциал развития многоэтажной жилой застройки",
            "Потенциал развития малоэтажной жилой застройки",
            "Потенциал развития жилой застройки типа ИЖС",
        ]

        if benchmarks.get("residential") is not None:
            present = [c for c in res_cols_detailed if c in gdf.columns]

            if not present:
                raise http_exception(
                    404,
                    "Missing detailed residential indicators for aggregating basic residential value",
                    list(requested_keys),
                    {"required_columns": res_cols_detailed},
                )

            gdf["Потенциал развития жилой застройки"] = (
                gdf[present].mean(axis=1).apply(math.ceil)
            )

        missing = [
            col
            for col in InvestmentPotentialService._required_columns(benchmarks)
            if col not in gdf.columns
        ]
        if missing:
            raise http_exception(
                404,
                "Required indicators for evaluation are missing on the territory",
                _input={"benchmarks": list(requested_keys)},
                _detail={"missing_indicators": missing},
            )

        if not as_long:
            return gdf.to_crs(gdf.estimate_utm_crs())

        records = (
            gdf.apply(
                lambda row: [
                    {
                        "ip_type": key,
                        "ip_value": row[LAND_USE_TO_POTENTIAL_COLUMN[key]],
                        "geometry": row.geometry,
                    }
                    for key in requested_keys
                ],
                axis=1,
            )
            .explode()
            .tolist()
        )

        if not records:
            return gpd.GeoDataFrame(
                columns=["ip_type", "ip_value", "geometry"],
                geometry="geometry",
                crs=gdf.crs,
            )

        long_gdf = gpd.GeoDataFrame(
            pd.DataFrame(records), geometry="geometry", crs=gdf.crs
        )
        logger.info(f"Indicator values fetched successfully for scenario {scenario_id}")
        return long_gdf.to_crs(long_gdf.estimate_utm_crs()).reset_index(drop=True)

    @staticmethod
    async def calculate_investment_attractiveness(
        gdf: gpd.GeoDataFrame, benchmarks: dict[str, dict[str, any]]
    ) -> gpd.GeoDataFrame | pd.DataFrame:
        benchmarks = {k: v for k, v in benchmarks.items() if v is not None}
        valid_keys = set(benchmarks.keys())
        mask = gdf["ip_type"].isin(valid_keys)
        gdf = gdf.loc[mask].copy()
        try:
            an = InvestmentAttractivenessAnalyzer(benchmarks=benchmarks)
            gdf_out, summary = an.calculate_investment_metrics(gdf)
            gdf_out = gdf_out.copy()
            gdf_out.loc[:, "ECON_NPV"] = gdf_out["ECON_NPV"].astype(float)
        except Exception as e:
            raise http_exception(
                500,
                "Error occurred while calculating investment attractiveness",
                _detail={"error": str(e)},
            )

        return gdf_out, summary

    @staticmethod
    async def map_zones(
        score_gdf: gpd.GeoDataFrame, zones_gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:

        try:
            ip_map: Dict[str, float] = score_gdf.set_index("ip_type")[
                "ip_value"
            ].to_dict()
            zone_map: Dict[str, int] = zone_mapping

            zone_to_ip = {v: k for k, v in zone_map.items()}
        except Exception as e:
            raise http_exception(500, "Error mapping zones", _detail={"error": str(e)})

        residential_keys_all = [
            "residential_individual",
            "residential_lowrise",
            "residential_midrise",
            "residential_multistorey",
            "residential",
        ]
        residential_keys = [k for k in residential_keys_all if k in ip_map]
        max_res_val: float | None = None
        if residential_keys:
            max_res_val = max(ip_map[k] for k in residential_keys)

        out = zones_gdf.copy()
        out = out.to_crs(out.estimate_utm_crs())
        out["ip_type"] = (
            out["zone_type_id"]
            .map(zone_to_ip)
            .fillna("residential_lowrise")
            .astype(str)
        )

        out["area"] = out.geometry.area

        def _resolve_value(zid: int, itype: str) -> float | None:
            if itype in residential_keys:
                return max_res_val
            return ip_map.get(itype)

        out["ip_value"] = out.apply(
            lambda row: _resolve_value(row["zone_type_id"], row["ip_type"]), axis=1
        )
        logger.info(f"Zone values have been calculated")
        return out

    @staticmethod
    async def generate_response(
        gdf_out: gpd.GeoDataFrame, summary: pd.DataFrame, as_geojson: bool = False
    ) -> List[Dict[str, Any]]:
        if not as_geojson:
            df = summary.rename_axis("land_use_type").reset_index()
            df["land_use_type_id"] = (
                df["land_use_type"].map(zone_mapping).astype("Int64")
            )
            records = df.to_dict(orient="records")

            cleaned = []
            for rec in records:
                new_rec = {
                    k: (None if isinstance(v, float) and pd.isna(v) else v)
                    for k, v in rec.items()
                }
                cleaned.append(new_rec)
            return cleaned

        gdf = gdf_out.to_crs(4326).copy()
        gdf["land_use_type_id"] = gdf["ip_type"].map(zone_mapping).astype("Int64")
        gdf = gdf.rename(columns={"ip_type": "land_use_type_name"})
        geojson_str = gdf.to_json()
        return json.loads(geojson_str)

    @staticmethod
    async def run_investment_calculation(
        scenario_id,
        as_geojson: bool,
        benchmarks: dict[str, dict[str, any]],
        token: str = None,
    ) -> gpd.GeoDataFrame | pd.DataFrame:
        logger.info(
            f"Running investment calculation "
            f"for scenario {scenario_id}, "
            f"as_geojson={as_geojson}, "
            f"benchmarks={benchmarks}"
        )
        territory_gdf = await UrbanAPIGateway.get_territory(scenario_id, token=token)
        territory_values_gdf = (
            await InvestmentPotentialService.get_territory_indicator_values(
                scenario_id, territory_gdf, token=token, benchmarks=benchmarks
            )
        )
        landuse_score_gdf = await InvestmentPotentialService.calculate_landuse_score(
            territory_values_gdf
        )
        gdf_out, summary = (
            await InvestmentPotentialService.calculate_investment_attractiveness(
                landuse_score_gdf, benchmarks
            )
        )
        response = await InvestmentPotentialService.generate_response(
            gdf_out, summary, as_geojson
        )
        return response

    @staticmethod
    async def run_investment_calculation_fzones(
        scenario_id,
        as_geojson: bool,
        benchmarks: dict[str, dict[str, any]],
        source: str = None,
        token: str = None,
        year: int = None,
    ) -> gpd.GeoDataFrame | pd.DataFrame:
        logger.info(
            f"Running investment calculation "
            f"for scenario {scenario_id}, "
            f"as_geojson={as_geojson}, "
            f"benchmarks={benchmarks}"
        )
        territory_gdf = await UrbanAPIGateway.get_territory(scenario_id, token=token)
        landuse_score_gdf = (
            await InvestmentPotentialService.get_territory_indicator_values(
                scenario_id,
                territory_gdf,
                benchmarks=benchmarks,
                as_long=True,
                token=token,
            )
        )
        functional_zones_gdf = await UrbanAPIGateway.get_functional_zones(
            scenario_id, source=source, token=token, year=year
        )
        mapped_zones_gdf = await InvestmentPotentialService.map_zones(
            landuse_score_gdf, functional_zones_gdf
        )
        mapped_zones_gdf = mapped_zones_gdf.to_crs(mapped_zones_gdf.estimate_utm_crs())
        gdf_out, summary = (
            await InvestmentPotentialService.calculate_investment_attractiveness(
                mapped_zones_gdf, benchmarks
            )
        )
        response = await InvestmentPotentialService.generate_response(
            gdf_out, summary, as_geojson
        )
        return response

    @staticmethod
    async def run_investment_calculation_coords(
        scenario_id,
        as_geojson: bool,
        benchmarks: dict[str, dict[str, any]],
        geojson: FeatureCollection,
        token: str = None,
    ) -> gpd.GeoDataFrame | pd.DataFrame:
        geojson_dict = geojson.as_geo_dict()
        gdf = gpd.GeoDataFrame.from_features(geojson_dict["features"])
        gdf = gdf.set_crs("EPSG:4326")
        logger.info(
            f"Running investment calculation "
            f"for scenario {scenario_id}, "
            f"as_geojson={as_geojson}, "
            f"benchmarks={benchmarks}, "
            f"Features: {geojson_dict}"
        )
        territory_gdf = await UrbanAPIGateway.get_territory(scenario_id, token=token)
        landuse_score_gdf = (
            await InvestmentPotentialService.get_territory_indicator_values(
                scenario_id,
                territory_gdf,
                benchmarks=benchmarks,
                as_long=True,
                token=token,
            )
        )
        mapped_zones_gdf = await InvestmentPotentialService.map_zones(
            landuse_score_gdf, gdf
        )
        mapped_zones_gdf = mapped_zones_gdf.to_crs(mapped_zones_gdf.estimate_utm_crs())
        gdf_out, summary = (
            await InvestmentPotentialService.calculate_investment_attractiveness(
                mapped_zones_gdf, benchmarks
            )
        )
        response = await InvestmentPotentialService.generate_response(
            gdf_out, summary, as_geojson
        )
        return response
