from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from app.enums.chart_type import ChartType


class AnalysisChartRequestDTO(BaseModel):
    dataset_id: str
    question: Optional[str] = None
    sql: Optional[str] = None
    chart_type: Optional[ChartType] = None
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    limit: Optional[int] = Field(default=100, ge=1, le=1000)

    @model_validator(mode="after")
    def validate_inputs(self) -> "AnalysisChartRequestDTO":
        has_explicit = bool(self.sql and self.chart_type and self.x_field and self.y_field)
        has_question = bool(self.question and self.question.strip())

        if not (has_explicit or has_question):
            raise ValueError(
                "Either provide a 'question' or explicit chart parameters ('sql', 'chart_type', 'x_field', 'y_field')."
            )
        return self


class ChartSpec(BaseModel):
    type: str
    title: str
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    series: List[str] = []
    data: List[Dict[str, Any]] = []


class AnalysisChartDataDTO(BaseModel):
    dataset_id: str
    chart_type: str
    title: str
    executed_sql: str
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    columns: List[str]
    rows: List[Dict[str, Any]]
    chart_spec: ChartSpec


class AnalysisChartResponseDTO(BaseModel):
    success: bool
    message: str
    data: Optional[AnalysisChartDataDTO] = None