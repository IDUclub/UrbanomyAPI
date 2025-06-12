from typing import Any, Dict

from pydantic import BaseModel, Field

residential_demo: Dict[str, Dict[str, Any]] = {
    "residential_individual": {
        "density": 0.25,
        "land_cost": 1500,
        "cost_build": 48000,
        "price_sale": 92000,
        "construction_years": 2,
        "sale_years": 3,
        "opex_rate": 800,
    },
    "residential_lowrise": {
        "density": 0.5,
        "land_cost": 1800,
        "cost_build": 50000,
        "price_sale": 95000,
        "construction_years": 2,
        "sale_years": 3,
        "opex_rate": 900,
    },
    "residential_midrise": {
        "density": 1.5,
        "land_cost": 2500,
        "cost_build": 55000,
        "price_sale": 105000,
        "construction_years": 3,
        "sale_years": 4,
        "opex_rate": 1200,
    },
    "residential_multistorey": {
        "density": 3.0,
        "land_cost": 3000,
        "cost_build": 62000,
        "price_sale": 120000,
        "construction_years": 4,
        "sale_years": 5,
        "opex_rate": 1500,
    },
}

non_residential_demo: Dict[str, Dict[str, Any]] = {
    "business": {
        "density": 2.0,
        "land_cost": 2800,
        "cost_build": 55000,
        "rent_annual": 14000,
        "rent_years": 12,
        "occupancy": 0.85,
        "construction_years": 3,
        "opex_rate": 1300,
    },
    "recreation": {
        "density": 0.2,
        "land_cost": 1000,
        "cost_build": 20000,
        "rent_annual": 6500,
        "rent_years": 15,
        "occupancy": 0.7,
        "construction_years": 2,
        "opex_rate": 1000,
    },
    "special": {
        "density": 1.0,
        "land_cost": 1200,
        "cost_build": 35000,
        "rent_annual": 8000,
        "rent_years": 15,
        "occupancy": 0.8,
        "construction_years": 3,
        "opex_rate": 1500,
    },
    "industrial": {
        "density": 1.0,
        "land_cost": 900,
        "cost_build": 38000,
        "rent_annual": 9800,
        "rent_years": 12,
        "occupancy": 0.9,
        "construction_years": 2,
        "opex_rate": 700,
    },
    "agriculture": {
        "density": 0.1,
        "land_cost": 300,
        "cost_build": 25000,
        "rent_annual": 2500,
        "rent_years": 15,
        "occupancy": 0.95,
        "construction_years": 1,
        "opex_rate": 300,
    },
    "transport": {
        "density": 1.2,
        "land_cost": 1100,
        "cost_build": 18000,
        "rent_annual": 4200,
        "rent_years": 15,
        "occupancy": 0.88,
        "construction_years": 3,
        "opex_rate": 600,
    },
}

# Модели под две группы
class ResidentialBenchmarkDto(BaseModel):
    density: float = Field(..., example=0.25)
    land_cost: int = Field(..., example=1500)
    cost_build: int = Field(..., example=48000)
    price_sale: int = Field(..., example=92000)
    construction_years: int = Field(..., example=2)
    sale_years: int = Field(..., example=3)
    opex_rate: int = Field(..., example=800)

class NonResidentialBenchmarkDto(BaseModel):
    density: float = Field(..., example=2.0)
    land_cost: int = Field(..., example=2800)
    cost_build: int = Field(..., example=55000)
    rent_annual: int = Field(..., example=14000)
    rent_years: int = Field(..., example=12)
    occupancy: float = Field(..., example=0.85)
    construction_years: int = Field(..., example=3)
    opex_rate: int = Field(..., example=1300)


class InvestmentAttractivenessRequestDto(BaseModel):
    scenario_id: int = Field(..., example=198, description="ID сценария")
    as_geojson: bool = Field(..., example=False, description="Which format to return")
    residential: Dict[str, ResidentialBenchmarkDto] = Field(
        default=residential_demo,
        description="Эталонные параметры для жилых категорий"
    )
    non_residential: Dict[str, NonResidentialBenchmarkDto] = Field(
        default=non_residential_demo,
        description="Эталонные параметры для остальных категорий"
    )
