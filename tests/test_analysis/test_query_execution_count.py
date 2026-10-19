"""SQL contracts use mocked asyncpg connections, never a PostgreSQL server."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import asyncpg
import pytest
from fastapi.testclient import TestClient

from app.core.analysis.query_count_workflow import QueryCountWorkflow
from app.database.query_execution_repository import QueryExecutionRepository
from app.main import app
from app.routes.analysis import query_count
from app.security import security

SECRET = "count-test-only-secret"
HEADERS = {"X-Signature": SECRET, "X-User-Id": "37"}


@pytest.fixture
def database():
    connection = SimpleNamespace(execute=AsyncMock(), fetchval=AsyncMock(return_value=0))
    pool = MagicMock()
    pool.acquire.return_value.__aenter__.return_value = connection
    return pool, connection


@pytest.mark.parametrize("user_id,count", [(37, 0), (91, 8)])
async def test_repository_count_filters_parameterized_owner(database, user_id, count):
    pool, connection = database
    connection.fetchval.return_value = count
    assert await QueryExecutionRepository(pool).count_by_user(user_id=user_id) == count
    connection.fetchval.assert_awaited_once()
    sql, *args = connection.fetchval.await_args.args
    assert " ".join(sql.split()).rstrip(";") == (
        "SELECT COUNT(*) FROM query_executions WHERE user_id = $1"
    )
    assert args == [user_id]
    assert connection.fetchval.await_args.kwargs == {}


async def test_repository_inserts_one_unique_record_per_execution(database):
    pool, connection = database
    repository = QueryExecutionRepository(pool)
    dataset_id = uuid4()
    for _ in range(2):
        await repository.record_success(user_id=37, dataset_id=dataset_id)
    assert connection.execute.await_count == 2
    ids = []
    for invocation in connection.execute.await_args_list:
        sql, execution_id, owner, dataset = invocation.args
        assert " ".join(sql.split()) == (
            "INSERT INTO query_executions (id, user_id, dataset_id) VALUES ($1, $2, $3)"
        )
        assert isinstance(execution_id, UUID)
        assert (owner, dataset) == (37, dataset_id)
        ids.append(execution_id)
    assert ids[0] != ids[1]


@pytest.mark.parametrize("operation", ["count_by_user", "record_success"])
async def test_repository_propagates_database_errors(database, operation):
    pool, connection = database
    connection.fetchval.side_effect = connection.execute.side_effect = asyncpg.PostgresError("offline")
    kwargs = {"user_id": 37}
    if operation == "record_success":
        kwargs["dataset_id"] = uuid4()
    with pytest.raises(asyncpg.PostgresError, match="offline"):
        await getattr(QueryExecutionRepository(pool), operation)(**kwargs)


@pytest.mark.parametrize("count", [0, 12])
async def test_count_workflow_forwards_identity(count):
    repository = SimpleNamespace(count_by_user=AsyncMock(return_value=count))
    assert await QueryCountWorkflow(repository).execute(user_id=91) == count
    repository.count_by_user.assert_awaited_once_with(user_id=91)


async def test_count_workflow_propagates_failure():
    repository = SimpleNamespace(count_by_user=AsyncMock(side_effect=asyncpg.PostgresError("offline")))
    with pytest.raises(asyncpg.PostgresError, match="offline"):
        await QueryCountWorkflow(repository).execute(user_id=37)


@pytest.fixture
def count_client(monkeypatch, database):
    pool, connection = database
    monkeypatch.setattr(query_count, "get_db_pool", AsyncMock(return_value=pool))
    monkeypatch.setattr(security, "get_settings", lambda: SimpleNamespace(
        security=SimpleNamespace(secret_key=SECRET),
    ))
    overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()
    try:
        with TestClient(app) as client:
            yield client, connection
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)


@pytest.mark.parametrize("user_id,count", [(37, 0), (91, 14)])
def test_count_http_real_composition_identity_and_no_store(count_client, user_id, count):
    client, connection = count_client
    connection.fetchval.return_value = count
    response = client.get("/api/v1/analysis/queries/count?user_id=666", headers={
        **HEADERS, "X-User-Id": str(user_id),
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"] == {"count": count}
    assert response.headers["cache-control"] == "no-store"
    connection.fetchval.assert_awaited_once()
    assert connection.fetchval.await_args.args[1:] == (user_id,)


@pytest.mark.parametrize("headers,status", [
    ({}, 422), ({"X-User-Id": "37"}, 422),
    ({"X-Signature": SECRET}, 422),
    ({**HEADERS, "X-Signature": "incorrect"}, 401),
    *[({**HEADERS, "X-User-Id": value}, 422) for value in ("", "abc", "0", "-1", "1.5", "true")],
])
def test_count_http_security(count_client, headers, status):
    client, connection = count_client
    response = client.get("/api/v1/analysis/queries/count", headers=headers)
    assert response.status_code == status
    connection.fetchval.assert_not_awaited()


def test_count_http_database_failure_is_not_zero(count_client):
    client, connection = count_client
    connection.fetchval.side_effect = asyncpg.PostgresError("private database error")
    response = client.get("/api/v1/analysis/queries/count", headers=HEADERS)
    assert response.status_code == 500
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["detail"]["success"] is False
    assert response.json()["detail"]["data"] is None
    assert "private database error" not in response.text
    connection.fetchval.assert_awaited_once()


async def test_count_dependency_composes_execution_repository(monkeypatch, database):
    pool, _ = database
    get_pool = AsyncMock(return_value=pool)
    monkeypatch.setattr(query_count, "get_db_pool", get_pool)
    controller = await query_count.get_query_count_controller()
    repository = controller.service.workflow.repository
    assert isinstance(repository, QueryExecutionRepository)
    assert repository.pool is pool
    get_pool.assert_awaited_once_with()


@pytest.mark.parametrize("failure,status", [("persist", 500), ("internal_sql", 500), ("invalid_sql", 400)])
def test_query_http_failure_never_returns_success(count_client, failure, status):
    from unittest.mock import Mock
    from app.analysis.dependencies import get_analysis_query_controller
    from app.analysis.sql_safety_validator import SQLSafetyValidator
    from app.core.analysis.workflow import AnalysisQueryWorkflow
    from app.adapters.analysis.duckdb_query_adapter import DuckDBQueryResult
    from app.prepare.exceptions import ValidationException
    from app.routes.analysis.controllers.controller import AnalysisQueryController
    from app.routes.analysis.services.service import AnalysisQueryService

    client, _ = count_client
    dataset_id = uuid4()
    dataset_repository = SimpleNamespace(get_by_id=AsyncMock(return_value=SimpleNamespace(
        user_id=37, status="PREPARED", prepared_object_key="prepared.parquet",
    )))
    storage = SimpleNamespace(read_file=AsyncMock(return_value=b"fake-parquet"))
    executor = Mock()
    executor.execute.return_value = DuckDBQueryResult(
        columns=[], rows=[], rows_count=0, returned_rows_count=0,
    )
    executions = SimpleNamespace(record_success=AsyncMock())
    if failure == "persist":
        executions.record_success.side_effect = asyncpg.PostgresError("write failed")
    else:
        executor.execute.side_effect = (
            ValidationException("Invalid analytical SQL") if failure == "invalid_sql"
            else RuntimeError("internal SQL failure")
        )
    logger = Mock()
    workflow = AnalysisQueryWorkflow(
        dataset_repository, storage, SQLSafetyValidator(), executor, logger, executions,
    )
    controller = AnalysisQueryController(AnalysisQueryService(workflow, logger), logger)
    app.dependency_overrides[get_analysis_query_controller] = lambda: controller
    response = client.post("/api/v1/analysis/query", headers=HEADERS, json={
        "dataset_id": str(dataset_id), "sql": "SELECT * FROM dataset",
    })
    assert response.status_code == status
    assert response.json()["detail"]["success"] is False
    assert response.json()["detail"]["data"] is None
    if failure == "persist":
        executions.record_success.assert_awaited_once_with(user_id=37, dataset_id=dataset_id)
    else:
        executions.record_success.assert_not_awaited()
