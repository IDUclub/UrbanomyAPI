# import json
# import geopandas as gpd
from typing import Annotated

from fastapi import APIRouter, FastAPI, Depends
# from fastapi.responses import JSONResponse

from app.common.exceptions.http_exception_wrapper import http_exception
from app.urbanomy_api.dto.investment_attractivness_dto import InvestmentAttractivenessDto
from app.urbanomy_api.modules.invest_potential_service import InvestmentPotentialService
# from app.urbanomy_api.modules.urban_api_gateway import UrbanAPIGateway

app = FastAPI()
urbanomic_router = APIRouter()


@urbanomic_router.post("/calculate_investment_attractiveness")
async def calculate_investment_attractiveness(
        request_info: Annotated[InvestmentAttractivenessDto, Depends(InvestmentAttractivenessDto)]
):
    scenario_id = request_info.scenario_id
    to_return = request_info.to_return
    benchmarks = request_info.benchmarks
    try:
        result = await InvestmentPotentialService.run_investment_calculation(
            scenario_id, to_return, benchmarks
        )
    except ValueError as e:
        raise http_exception(400, str(e))

    return result


@urbanomic_router.post("/calculate_investment_attractiveness_functional_zones")
async def calculate_investment_attractiveness_functional_zones(
        request_info: InvestmentAttractivenessDto
):
    scenario_id = request_info.scenario_id
    to_return = request_info.to_return
    benchmarks = request_info.benchmarks
    try:
        result = await InvestmentPotentialService.run_investment_calculation_fzones(
            scenario_id, to_return, benchmarks
        )
    except ValueError as e:
        raise http_exception(400, str(e))

    return result

# @urbanomic_router.post("/calculate_investment_attractiveness_functional_zones")
# async def calculate_investment_attractiveness_by_coords()
