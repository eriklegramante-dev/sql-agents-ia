"""Unit tests for the analysis chart generation service and workflows."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.enums.chart_type import ChartType
from app.enums.dataset_status import DatasetStatus
from app.routes.analysis.dtos.dto import AnalysisChartRequestDTO
from app.routes.analysis.helpers.chart_planner import ChartPlannerTool
from app.routes.analysis.protocols import QueryResult
from app.routes.analysis.services.service import AnalysisService


@pytest.fixture
def mock_dataset_repo() -> MagicMock:
    """Provides a mocked dataset repository."""
    repo = MagicMock()
    mock_dataset = MagicMock()
    mock_dataset.id = uuid4()
    mock_dataset.status = DatasetStatus.PREPARED
    mock_dataset.table_name = "t_sample_table"
    mock_dataset.columns = ["category", "total"]
    repo.find_by_id = AsyncMock(return_value=mock_dataset)
    return repo


@pytest.fixture
def mock_query_adapter() -> MagicMock:
    """Provides a mocked query adapter returning typed QueryResult."""
    adapter = MagicMock()
    adapter.execute_query = AsyncMock(
        return_value=QueryResult(
            columns=["category", "total"],
            rows=[
                {"category": "Category A", "total": 100},
                {"category": "Category B", "total": 200},
            ],
        )
    )
    return adapter


@pytest.fixture
def planner_tool() -> ChartPlannerTool:
    """Provides a ChartPlannerTool instance."""
    return ChartPlannerTool()


@pytest.mark.anyio
async def test_generate_chart_explicit_success(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    planner_tool: ChartPlannerTool,
) -> None:
    """Tests successful chart generation with explicit SQL parameters."""
    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
        planner_tool=planner_tool,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=uuid4(),
        sql="SELECT category, total FROM t_sample_table",
        chart_type=ChartType.BAR,
        x_field="category",
        y_field="total",
    )

    response = await service.generate_chart(payload)

    assert response.success is True
    assert response.data is not None
    assert response.data.chart_type == ChartType.BAR
    assert response.data.x_field == "category"
    assert response.data.y_field == "total"
    assert len(response.data.rows) == 2


@pytest.mark.anyio
async def test_generate_chart_question_success(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    planner_tool: ChartPlannerTool,
) -> None:
    """Tests question-based chart inference and execution."""
    mock_query_adapter.execute_query = AsyncMock(
        return_value=QueryResult(
            columns=["category", "total"],
            rows=[
                {"category": "Electronics", "total": 10},
                {"category": "Books", "total": 5},
            ],
        )
    )

    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
        planner_tool=planner_tool,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=uuid4(),
        question="Show total count per category",
    )

    response = await service.generate_chart(payload)

    assert response.success is True
    assert response.data is not None
    assert response.data.x_field == "category"
    assert response.data.y_field == "total"


@pytest.mark.anyio
async def test_generate_chart_rejects_unprepared_dataset(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    planner_tool: ChartPlannerTool,
) -> None:
    """Tests failure when dataset is in an unprepared status."""
    mock_dataset = MagicMock()
    mock_dataset.status = DatasetStatus.UPLOADING
    mock_dataset_repo.find_by_id = AsyncMock(return_value=mock_dataset)

    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
        planner_tool=planner_tool,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=uuid4(),
        sql="SELECT category, total FROM t_sample_table",
        chart_type=ChartType.BAR,
        x_field="category",
        y_field="total",
    )

    response = await service.generate_chart(payload)

    assert response.success is False
    assert "not prepared" in response.message.lower()
    assert response.data is None


@pytest.mark.anyio
async def test_generate_chart_rejects_unsafe_sql(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    planner_tool: ChartPlannerTool,
) -> None:
    """Tests security validator rejection on mutating statements."""
    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
        planner_tool=planner_tool,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=uuid4(),
        sql="DELETE FROM t_sample_table",
        chart_type=ChartType.BAR,
        x_field="category",
        y_field="total",
    )

    with pytest.raises(ValueError, match="Only read-only SELECT queries are allowed"):
        await service.generate_chart(payload)


@pytest.mark.anyio
async def test_generate_chart_missing_fields_validation(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    planner_tool: ChartPlannerTool,
) -> None:
    """Tests failure when mapped chart axis field is missing from result columns."""
    mock_query_adapter.execute_query = AsyncMock(
        return_value=QueryResult(
            columns=["category", "total"],
            rows=[],
        )
    )

    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
        planner_tool=planner_tool,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=uuid4(),
        sql="SELECT category, total FROM t_sample_table",
        chart_type=ChartType.BAR,
        x_field="non_existent_column",
        y_field="total",
    )

    response = await service.generate_chart(payload)

    assert response.success is False
    assert "was not found in query results" in response.message
    assert response.data is None
