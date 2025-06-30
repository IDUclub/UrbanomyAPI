from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, FastAPI

from app.common.auth.auth import verify_token
from app.urbanomy_api.dto.benchmarks_dto import (non_residential_demo,
                                                 residential_demo)
from app.urbanomy_api.dto.investment_attractivness_dto import \
    InvestmentAttractivenessRequestDTO
from app.urbanomy_api.dto.InvestmentAttractivnessFzonesRequestDto import \
    InvestmentAttractivenessFunctionalZonesRequestDTO
from app.urbanomy_api.dto.investments_attractivness_coords_dto import \
    InvestmentAttractivenessCoordsDto
from app.urbanomy_api.modules.invest_potential_service import \
    InvestmentPotentialService

app = FastAPI()
urbanomic_router = APIRouter()


@urbanomic_router.post("/calculate_investment_attractiveness")
async def calculate_investment_attractiveness(
    params: Annotated[
        InvestmentAttractivenessRequestDTO, Depends(InvestmentAttractivenessRequestDTO)
    ],
    token: str = Depends(verify_token),
):
    benchmarks_dict: Dict[str, Dict[str, Any]] = params.benchmarks.model_dump()
    result = await InvestmentPotentialService.run_investment_calculation(
        params.scenario_id, params.as_geojson, benchmarks_dict, token
    )
    return result


@urbanomic_router.post("/calculate_investment_attractiveness_functional_zones")
async def calculate_investment_attractiveness_functional_zones(
    params: Annotated[
        InvestmentAttractivenessFunctionalZonesRequestDTO,
        Depends(InvestmentAttractivenessFunctionalZonesRequestDTO),
    ],
    token: str = Depends(verify_token),
):
    benchmarks_dict: Dict[str, Dict[str, Any]] = params.benchmarks.model_dump()
    result = await InvestmentPotentialService.run_investment_calculation_fzones(
        params.scenario_id, params.as_geojson, benchmarks_dict, params.source, token
    )

    return result


@urbanomic_router.post("/calculate_investment_attractiveness_coords")
async def calculate_investment_attractiveness_by_coords(
    params: Annotated[
        InvestmentAttractivenessCoordsDto, Depends(InvestmentAttractivenessCoordsDto)
    ],
    token: str = Depends(verify_token),
):
    benchmarks_dict: Dict[str, Dict[str, Any]] = params.benchmarks.model_dump()
    result = await InvestmentPotentialService.run_investment_calculation_coords(
        params.scenario_id, params.as_geojson, benchmarks_dict, params.geometry, token
    )
    return result


@urbanomic_router.get("/get_benchmarks_defaults")
async def get_benchmarks_defaults():
    benchmarks_dict = {**residential_demo, **non_residential_demo}
    return benchmarks_dict
