import json
from pydantic import BaseModel, Field

with open("app/urbanomy_api/schemas/benchmarks.json", "r") as et:
    benchmarks = json.load(et)

residential_demo = benchmarks["residential_demo"]
non_residential_demo = benchmarks["non_residential_demo"]


class ResidentialBenchmarkDtoPrimitive(BaseModel):
    density: float = Field(..., example=0.25)
    land_cost: int = Field(..., example=1500)
    cost_build: int = Field(..., example=48000)
    price_sale: int = Field(..., example=92000)
    construction_years: int = Field(..., example=2)
    sale_years: int = Field(..., example=3)
    opex_rate: int = Field(..., example=800)


class NonResidentialBenchmarkDtoPrimitive(BaseModel):
    density: float = Field(..., example=2.0)
    land_cost: int = Field(..., example=2800)
    cost_build: int = Field(..., example=55000)
    rent_annual: int = Field(..., example=14000)
    rent_years: int = Field(..., example=12)
    occupancy: float = Field(..., example=0.85)
    construction_years: int = Field(..., example=3)
    opex_rate: int = Field(..., example=1300)


class BenchmarksDto(BaseModel):
    residential: ResidentialBenchmarkDtoPrimitive
    residential_individual: ResidentialBenchmarkDtoPrimitive
    residential_lowrise: ResidentialBenchmarkDtoPrimitive
    residential_midrise: ResidentialBenchmarkDtoPrimitive
    residential_multistorey: ResidentialBenchmarkDtoPrimitive

    business: NonResidentialBenchmarkDtoPrimitive
    recreation: NonResidentialBenchmarkDtoPrimitive
    special: NonResidentialBenchmarkDtoPrimitive
    industrial: NonResidentialBenchmarkDtoPrimitive
    agriculture: NonResidentialBenchmarkDtoPrimitive
    transport: NonResidentialBenchmarkDtoPrimitive

    class BenchmarksConfig:
        json_schema_extra = {
            "example": {
                **residential_demo,
                **non_residential_demo
            }
        }
