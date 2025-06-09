from typing import Any

from pydantic import BaseModel, Field

benchmarks_demo = {
    "residential_individual": {
        "density": 0.25,
        "land_cost": 1500,
        "cost_build": 48_000,
        "price_sale": 92_000,
        "construction_years": 2,
        "sale_years": 3,
        "opex_rate": 800,
    },
    "residential_lowrise": {
        "density": 0.5,
        "land_cost": 1800,
        "cost_build": 50_000,
        "price_sale": 95_000,
        "construction_years": 2,
        "sale_years": 3,
        "opex_rate": 900,
    },
    "residential_midrise": {
        "density": 1.5,
        "land_cost": 2500,
        "cost_build": 55_000,
        "price_sale": 105_000,
        "construction_years": 3,
        "sale_years": 4,
        "opex_rate": 1200,
    },
    "residential_multistorey": {
        "density": 3.0,
        "land_cost": 3000,
        "cost_build": 62_000,
        "price_sale": 120_000,
        "construction_years": 4,
        "sale_years": 5,
        "opex_rate": 1500,
    },
    "business": {
        "density": 2.0,
        "land_cost": 2800,
        "cost_build": 55_000,
        "rent_annual": 14_000,
        "rent_years": 12,
        "occupancy": 0.85,
        "construction_years": 3,
        "opex_rate": 1300,
    },
    "recreation": {
        "density": 0.2,
        "land_cost": 1000,
        "cost_build": 20_000,
        "rent_annual": 6_500,
        "rent_years": 15,
        "occupancy": 0.7,
        "construction_years": 2,
        "opex_rate": 1000,
    },
    "special": {
        "density": 1.0,
        "land_cost": 1200,
        "cost_build": 35_000,
        "rent_annual": 8_000,
        "rent_years": 15,
        "occupancy": 0.8,
        "construction_years": 3,
        "opex_rate": 1500,
    },
    "industrial": {
        "density": 1.0,
        "land_cost": 900,
        "cost_build": 38_000,
        "rent_annual": 9_800,
        "rent_years": 12,
        "occupancy": 0.9,
        "construction_years": 2,
        "opex_rate": 700,
    },
    "agriculture": {
        "density": 0.1,
        "land_cost": 300,
        "cost_build": 25_000,
        "rent_annual": 2_500,
        "rent_years": 15,
        "occupancy": 0.95,
        "construction_years": 1,
        "opex_rate": 300,
    },
    "transport": {
        "density": 1.2,
        "land_cost": 1100,
        "cost_build": 18_000,
        "rent_annual": 4_200,
        "rent_years": 15,
        "occupancy": 0.88,
        "construction_years": 3,
        "opex_rate": 600,
    },
}


class InvestmentAttractivenessDto(BaseModel):
    scenario_id: int = Field(..., example=198, description="Scenario ID")
    to_return: str = Field(..., example="geodataframe", description="Какой формат результата вернуть")
    benchmarks: dict[str, dict[str, Any]] = Field(
        ...,
        example=benchmarks_demo,
        description="Словарь бенчмарков для каждой категории"
    )
