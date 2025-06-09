# from typing import Any
#
# from pydantic import BaseModel, Field
#
#
#
# class InvestmentAttractivenessCoordsDto(BaseModel):
#     scenario_id: int = Field(..., example=198, description="Scenario ID")
#     to_return: str = Field(..., example="geodataframe", description="Какой формат результата вернуть")
#     benchmarks: dict[str, dict[str, Any]] = Field(
#         ...,
#         example=benchmarks_demo,
#         description="Словарь бенчмарков для каждой категории"
#     )