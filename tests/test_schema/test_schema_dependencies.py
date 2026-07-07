import asyncio
from types import SimpleNamespace

from app.database.dataset_repository import DatasetRepository
from app.routes.schema.controllers.controller import DatasetSchemaController
from app.routes.schema.dependencies import dependence
from app.routes.schema.services.service import DatasetSchemaService
from app.core.schema.workflow import DatasetSchemaWorkflow


def make_settings():
    return SimpleNamespace(
        database=SimpleNamespace(
            host="localhost",
            port=5432,
            name="sql_agents",
            user="postgres",
            password="password",
            min_pool_size=1,
            max_pool_size=5,
        ),
    )


def test_get_db_pool_creates_pool_when_db_pool_is_none(monkeypatch):
    expected_pool = object()
    create_pool_calls = []

    async def fake_create_pool(**kwargs):
        create_pool_calls.append(kwargs)
        return expected_pool

    monkeypatch.setattr(dependence, "_db_pool", None)
    monkeypatch.setattr(dependence, "get_settings", lambda: make_settings())
    monkeypatch.setattr(dependence.asyncpg, "create_pool", fake_create_pool)

    pool = asyncio.run(dependence.get_db_pool())

    assert pool is expected_pool
    assert dependence._db_pool is expected_pool
    assert create_pool_calls == [
        {
            "host": "localhost",
            "port": 5432,
            "database": "sql_agents",
            "user": "postgres",
            "password": "password",
            "min_size": 1,
            "max_size": 5,
        }
    ]


def test_get_db_pool_reuses_pool_when_it_already_exists(monkeypatch):
    existing_pool = object()

    async def fail_create_pool(**kwargs):
        raise AssertionError("create_pool should not be called")

    monkeypatch.setattr(dependence, "_db_pool", existing_pool)
    monkeypatch.setattr(dependence.asyncpg, "create_pool", fail_create_pool)

    pool = asyncio.run(dependence.get_db_pool())

    assert pool is existing_pool


def test_get_dataset_repository_returns_dataset_repository(monkeypatch):
    expected_pool = object()

    async def fake_get_db_pool():
        return expected_pool

    monkeypatch.setattr(dependence, "get_db_pool", fake_get_db_pool)

    repository = asyncio.run(dependence.get_dataset_repository())

    assert isinstance(repository, DatasetRepository)
    assert repository.pool is expected_pool


def test_get_dataset_schema_controller_returns_dataset_schema_controller(monkeypatch):
    repository = object()

    async def fake_get_dataset_repository():
        return repository

    monkeypatch.setattr(
        dependence,
        "get_dataset_repository",
        fake_get_dataset_repository,
    )

    controller = asyncio.run(dependence.get_dataset_schema_controller())

    assert isinstance(controller, DatasetSchemaController)
    assert isinstance(controller.service, DatasetSchemaService)
    assert isinstance(controller.service.workflow, DatasetSchemaWorkflow)
    assert controller.service.workflow.repository is repository
