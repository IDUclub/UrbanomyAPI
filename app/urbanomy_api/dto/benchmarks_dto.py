import json
from typing import Optional

from pydantic import BaseModel

with open("app/urbanomy_api/schemas/benchmarks.json", "r") as et:
    benchmarks = json.load(et)

residential_demo = benchmarks["residential_demo"]
non_residential_demo = benchmarks["non_residential_demo"]


class ResidentialBenchmark(BaseModel):
    density: float
    land_cost: int
    cost_build: int
    price_sale: int
    construction_years: int
    sale_years: int
    opex_rate: int


class NonResidentialBenchmark(BaseModel):
    density: float
    land_cost: int
    cost_build: int
    rent_annual: int
    rent_years: int
    occupancy: float
    construction_years: int
    opex_rate: int


class BenchmarksDto(BaseModel):
    residential: Optional[ResidentialBenchmark] = None
    residential_individual: Optional[ResidentialBenchmark] = None
    residential_lowrise: Optional[ResidentialBenchmark] = None
    residential_midrise: Optional[ResidentialBenchmark] = None
    residential_multistorey: Optional[ResidentialBenchmark] = None

    business: Optional[NonResidentialBenchmark] = None
    recreation: Optional[NonResidentialBenchmark] = None
    special: Optional[NonResidentialBenchmark] = None
    industrial: Optional[NonResidentialBenchmark] = None
    agriculture: Optional[NonResidentialBenchmark] = None
    transport: Optional[NonResidentialBenchmark] = None
