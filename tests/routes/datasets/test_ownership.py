"""Owner authorization with isolated repositories and storage adapters."""
from dataclasses import replace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.datasets.workflow import DatasetWorkflow
from app.core.datasets.deletion_workflow import DatasetDeletionWorkflow
from app.core.prepare.workflow import DatasetPreparationWorkflow
from app.core.profiling.workflow import DatasetProfileWorkflow
from app.main import app
from app.routes.datasets.dependencies.dependence import get_dataset_controller
from app.prepare.dependencies import get_dataset_preparation_controller
from app.profiling.dependencies import get_dataset_profile_controller

from app.prepare.exceptions import NotFoundException
from tests.core.datasets.test_workflow import make_dataset


@pytest.mark.parametrize('operation', ['get', 'delete', 'prepare', 'profile'])
@pytest.mark.parametrize('owner', [None, 99, 'missing'])
@pytest.mark.parametrize('status', ['COMPLETED', 'DELETED'])
async def test_denial_precedes_state_storage_calculation_and_mutations(operation, owner, status):
    dataset = None if owner == 'missing' else replace(make_dataset(), user_id=owner, status=status)
    repository = Mock()
    repository.get_metadata_by_id = AsyncMock(return_value=dataset)
    repository.get_by_id = AsyncMock(return_value=dataset)
    repository.update_status = AsyncMock()
    repository.delete_related_records = AsyncMock()
    repository.save_schema = AsyncMock()
    repository.update_prepared_info = AsyncMock()
    repository.save_profile = AsyncMock()
    storage = Mock(read_file=AsyncMock(), write_file=AsyncMock(), delete_file=AsyncMock())
    calculator = Mock()
    workflows = {
        'get': lambda: DatasetWorkflow(repository),
        'delete': lambda: DatasetDeletionWorkflow(repository, storage, 'raw', Mock()),
        'prepare': lambda: DatasetPreparationWorkflow(repository, storage),
        'profile': lambda: DatasetProfileWorkflow(repository, storage, calculator),
    }
    with pytest.raises(NotFoundException):
        await workflows[operation]().execute(uuid4(), user_id=17)
    expected_read = 'get_metadata_by_id' if operation in ('get', 'delete') else 'get_by_id'
    assert [call[0] for call in repository.mock_calls] == [expected_read]
    assert storage.mock_calls == []
    assert calculator.mock_calls == []



@pytest.mark.parametrize('method,suffix,dependency,operation', [
    ('get', '', get_dataset_controller, 'get_dataset'),
    ('delete', '', get_dataset_controller, 'delete_dataset'),
    ('post', '/prepare', get_dataset_preparation_controller, 'prepare_dataset'),
    ('post', '/profile', get_dataset_profile_controller, 'profile_dataset'),
])
@pytest.mark.parametrize('headers,expected', [
    ({}, 422),
    ({'X-User-Id': '17', 'X-Signature': 'wrong'}, 401),
    ({'X-User-Id': '17'}, 422),
    ({'X-Signature': 'dummy_secret_token'}, 422),
    ({'X-User-Id': '0', 'X-Signature': 'dummy_secret_token'}, 422),
    ({'X-User-Id': '17', 'X-Signature': 'dummy_secret_token'}, 404),
])
def test_route_authentication_and_identity(client, method, suffix, dependency, operation, headers, expected):
    controller = Mock()
    handler = AsyncMock(side_effect=NotFoundException('Dataset not found.'))
    setattr(controller, operation, handler)
    dataset_id = uuid4()
    original = app.dependency_overrides.copy()
    app.dependency_overrides[dependency] = lambda: controller
    try:
        response = getattr(client, method)(
            f'/api/v1/datasets/{dataset_id}{suffix}?user_id=99', headers=headers,
        )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original)
    assert response.status_code == expected
    if expected == 404:
        if operation in ('get_dataset', 'delete_dataset'):
            handler.assert_awaited_once_with(dataset_id=dataset_id, user_id=17)
        else:
            handler.assert_awaited_once_with(dataset_id, user_id=17)
        assert response.json()['detail'] == {
            'success': False, 'message': 'Dataset not found.', 'data': None, 'errors': [],
        }
    else:
        handler.assert_not_awaited()
