from typing import Annotated, Dict, Any

from fastapi import APIRouter, FastAPI, Depends

from app.urbanomy_api.dto.investment_attractivness_dto import InvestmentAttractivenessRequestDto
from app.urbanomy_api.dto.investments_attractivness_coords_dto import InvestmentAttractivenessCoordsDto
from app.urbanomy_api.modules.invest_potential_service import InvestmentPotentialService

app = FastAPI()
urbanomic_router = APIRouter()


@urbanomic_router.post("/calculate_investment_attractiveness")
async def calculate_investment_attractiveness(
    params: Annotated[InvestmentAttractivenessRequestDto, Depends(InvestmentAttractivenessRequestDto)]
):
    benchmarks_dict: Dict[str, Dict[str, Any]] = params.benchmarks.model_dump()
    result = await InvestmentPotentialService.run_investment_calculation(
        params.scenario_id,
        params.as_geojson,
        benchmarks_dict
    )
    return result


@urbanomic_router.post("/calculate_investment_attractiveness_functional_zones")
async def calculate_investment_attractiveness_functional_zones(
        params: Annotated[InvestmentAttractivenessRequestDto, Depends(InvestmentAttractivenessRequestDto)],
):
    benchmarks_dict: Dict[str, Dict[str, Any]] = params.benchmarks.model_dump()
    result = await InvestmentPotentialService.run_investment_calculation_fzones(
        params.scenario_id,
        params.as_geojson,
        benchmarks_dict
    )

    return result


@urbanomic_router.post("/calculate_investment_attractiveness_coords")
async def calculate_investment_attractiveness_by_coords(
        params: Annotated[InvestmentAttractivenessCoordsDto, Depends(InvestmentAttractivenessCoordsDto)],
):
    benchmarks_dict: Dict[str, Dict[str, Any]] = params.benchmarks.model_dump()
    result = await InvestmentPotentialService.run_investment_calculation_coords(
        params.scenario_id,
        params.as_geojson,
        benchmarks_dict,
        params.geometry)
    return result
