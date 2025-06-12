from typing import Annotated

from fastapi import APIRouter, FastAPI, Body

from app.urbanomy_api.dto.investment_attractivness_dto import InvestmentAttractivenessRequestDto
from app.urbanomy_api.dto.investments_attractivness_coords_dto import InvestmentAttractivenessCoordsDto
from app.urbanomy_api.modules.invest_potential_service import InvestmentPotentialService

app = FastAPI()
urbanomic_router = APIRouter()


@urbanomic_router.post("/calculate_investment_attractiveness")
async def calculate_investment_attractiveness(
        params: Annotated[InvestmentAttractivenessRequestDto, Body(...)],
):
    benchmarks_dict = {
        **{k: v.dict() for k, v in params.residential.items()},
        **{k: v.dict() for k, v in params.non_residential.items()}
    }

    result = await InvestmentPotentialService.run_investment_calculation(
        params.scenario_id,
        params.as_geojson,
        benchmarks_dict
    )
    return result


@urbanomic_router.post("/calculate_investment_attractiveness_functional_zones")
async def calculate_investment_attractiveness_functional_zones(
        params: Annotated[InvestmentAttractivenessRequestDto, Body(...)],
):
    benchmarks_dict = {
        **{k: v.dict() for k, v in params.residential.items()},
        **{k: v.dict() for k, v in params.non_residential.items()}
    }

    result = await InvestmentPotentialService.run_investment_calculation_fzones(
        params.scenario_id,
        params.as_geojson,
        benchmarks_dict
    )

    return result


@urbanomic_router.post("/calculate_investment_attractiveness_coords")
async def calculate_investment_attractiveness_by_coords(
        dto: Annotated[InvestmentAttractivenessCoordsDto, Body(...)],
):
    benchmarks_dict = {
        **{k: v.dict() for k, v in dto.residential.items()},
        **{k: v.dict() for k, v in dto.non_residential.items()}
    }

    result = await InvestmentPotentialService.run_investment_calculation_coords(dto.scenario_id, dto.as_geojson,
                                                                                benchmarks_dict, dto.geometry)
    return result
