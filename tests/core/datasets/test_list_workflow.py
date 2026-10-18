from unittest.mock import AsyncMock

import pytest

from app.core.datasets.list_workflow import DatasetListWorkflow
from app.core.datasets.repository import DatasetRepository


@pytest.mark.parametrize("datasets", [[], [object(), object()]])
async def test_list_workflow_forwards_user_id_and_preserves_results(datasets):
    repository = AsyncMock(spec=DatasetRepository)
    repository.list_metadata.return_value = datasets
    workflow = DatasetListWorkflow(dataset_repository=repository)

    result = await workflow.execute(user_id=37)

    repository.list_metadata.assert_awaited_once_with(user_id=37)
    assert result is datasets
