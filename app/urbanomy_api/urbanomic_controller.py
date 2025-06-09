from fastapi import APIRouter, FastAPI, Depends, Body

from app.common.exceptions.http_exception_wrapper import http_exception
from app.urbanomy_api.dto.investment_attractivness_dto import InvestmentAttractivenessQueryDto, \
    InvestmentAttractivenessBodyDto
from app.urbanomy_api.dto.investments_attractivness_coords_dto import InvestmentAttractivenessCoordsBody, \
    InvestmentAttractivenessCoordsDto
from app.urbanomy_api.modules.invest_potential_service import InvestmentPotentialService

app = FastAPI()
urbanomic_router = APIRouter()

#TODO rename to_return and change it to bool

@urbanomic_router.post("/calculate_investment_attractiveness")
async def calculate_investment_attractiveness(
        query: InvestmentAttractivenessQueryDto = Depends(),
        body: InvestmentAttractivenessBodyDto = Body(...),
):
    try:
        result = await InvestmentPotentialService.run_investment_calculation(
            query.scenario_id, query.to_return, body.benchmarks
        )
    except ValueError as e:
        raise http_exception(400, str(e))

    return result


@urbanomic_router.post("/calculate_investment_attractiveness_functional_zones")
async def calculate_investment_attractiveness_functional_zones(
        query: InvestmentAttractivenessQueryDto = Depends(),
        body: InvestmentAttractivenessBodyDto = Body(...)
):
    try:
        result = await InvestmentPotentialService.run_investment_calculation_fzones(
            query.scenario_id, query.to_return, body.benchmarks
        )
    except ValueError as e:
        raise http_exception(400, str(e))

    return result


@urbanomic_router.post("/calculate_investment_attractiveness_coords")
async def calculate_investment_attractiveness_by_coords(
        dto: InvestmentAttractivenessCoordsDto = Depends(),
        body: InvestmentAttractivenessCoordsBody = Body(...),
):
    scenario = dto.scenario_id
    fmt = dto.to_return
    benchmarks = body.benchmarks
    geo = body.geometry

    result = await InvestmentPotentialService.run_investment_calculation_coords(scenario, fmt, benchmarks, geo)
    return result
