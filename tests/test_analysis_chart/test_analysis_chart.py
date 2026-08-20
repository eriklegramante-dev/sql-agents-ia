"""Unit tests for dataset analysis chart generation."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest

from app.enums.chart_type import ChartType
from app.enums.dataset_status import DatasetStatus
from app.routes.analysis.dtos.dto import AnalysisChartRequestDTO
from app.routes.analysis.services.service import AnalysisService


@pytest.fixture
def sample_dataset_id() -> str:
    """Provides a valid UUID string for tests."""
    return str(uuid4())


@pytest.fixture
def mock_dataset_repo(sample_dataset_id: str) -> MagicMock:
    repo = MagicMock()
    mock_dataset = MagicMock()
    mock_dataset.id = sample_dataset_id
    mock_dataset.status = DatasetStatus.PREPARED
    mock_dataset.table_name = "t_sample_data"
    mock_dataset.columns = ["category", "total_sales"]
    repo.find_by_id = AsyncMock(return_value=mock_dataset)
    return repo


@pytest.fixture
def mock_query_adapter() -> MagicMock:
    """Mocks analytical query execution adapter."""
    adapter = MagicMock()
    adapter.execute_query = AsyncMock(
        return_value={
            "columns": ["category", "total_sales"],
            "rows": [
                {"category": "Electronics", "total_sales": 1500},
                {"category": "Books", "total_sales": 800},
            ],
        }
    )
    return adapter


@pytest.mark.asyncio
async def test_generate_chart_explicit_success(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    sample_dataset_id: str,
) -> None:
    """Tests successful chart generation with explicit SQL parameters."""
    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=sample_dataset_id,
        sql="SELECT category, total_sales FROM t_sample_data",
        chart_type=ChartType.BAR,
        x_field="category",
        y_field="total_sales",
        limit=50,
    )

    result = await service.generate_chart(payload)

    assert result.dataset_id == sample_dataset_id
    assert result.chart_type == "bar"
    assert result.chart_spec.x_field == "category"
    assert result.chart_spec.y_field == "total_sales"
    assert len(result.rows) == 2


@pytest.mark.asyncio
async def test_generate_chart_question_success(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    sample_dataset_id: str,
) -> None:
    """Tests question-based chart inference and execution."""
    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=sample_dataset_id,
        question="Show total sales distribution by category",
    )

    result = await service.generate_chart(payload)

    assert result.dataset_id == sample_dataset_id
    assert result.chart_type == "bar"
    assert result.chart_spec.data is not None


@pytest.mark.asyncio
async def test_generate_chart_rejects_unprepared_dataset(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    sample_dataset_id: str,
) -> None:
    """Tests failure when dataset is in uploaded/pending status."""
    mock_dataset = MagicMock()
    mock_dataset.status = DatasetStatus.UPLOADED
    mock_dataset_repo.find_by_id = AsyncMock(return_value=mock_dataset)

    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=sample_dataset_id,
        question="Show sales",
    )

    with pytest.raises(ValueError, match="must be prepared or profiled"):
        await service.generate_chart(payload)


@pytest.mark.asyncio
async def test_generate_chart_rejects_unsafe_sql(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    sample_dataset_id: str,
) -> None:
    """Tests security validator rejection on mutating statements."""
    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=sample_dataset_id,
        sql="DROP TABLE t_sample_data",
        chart_type=ChartType.BAR,
        x_field="category",
        y_field="total_sales",
    )

    with pytest.raises(ValueError, match="Only analytical SELECT"):
        await service.generate_chart(payload)


@pytest.mark.asyncio
async def test_generate_chart_missing_fields_validation(
    mock_dataset_repo: MagicMock,
    mock_query_adapter: MagicMock,
    sample_dataset_id: str,
) -> None:
    """Tests failure when mapped chart axis field is missing from result columns."""
    service = AnalysisService(
        dataset_repo=mock_dataset_repo,
        query_adapter=mock_query_adapter,
    )
    payload = AnalysisChartRequestDTO(
        dataset_id=sample_dataset_id,
        sql="SELECT category, total_sales FROM t_sample_data",
        chart_type=ChartType.BAR,
        x_field="non_existing_col",
        y_field="total_sales",
    )

    with pytest.raises(ValueError, match="was not found in query results"):
        await service.generate_chart(payload)