import asyncio

from app.adapters.analysis.duckdb_query_adapter import DuckDBQueryAdapter
from app.analysis import dependencies
from app.analysis.sql_safety_validator import SQLSafetyValidator
from app.core.analysis.workflow import AnalysisQueryWorkflow
from app.routes.analysis.controllers.controller import AnalysisQueryController
from app.routes.analysis.services.service import AnalysisQueryService


def test_get_analysis_query_workflow_returns_analysis_query_workflow(monkeypatch):
    repository = object()
    storage_adapter = object()

    async def fake_get_dataset_repository():
        return repository

    async def fake_get_storage_adapter():
        return storage_adapter

    monkeypatch.setattr(
        dependencies,
        "get_dataset_repository",
        fake_get_dataset_repository,
    )
    monkeypatch.setattr(
        dependencies,
        "get_storage_adapter",
        fake_get_storage_adapter,
    )

    workflow = asyncio.run(dependencies.get_analysis_query_workflow())

    assert isinstance(workflow, AnalysisQueryWorkflow)
    assert workflow.dataset_repository is repository
    assert workflow.storage_adapter is storage_adapter
    assert isinstance(workflow.sql_validator, SQLSafetyValidator)
    assert isinstance(workflow.query_adapter, DuckDBQueryAdapter)


def test_get_analysis_query_service_returns_analysis_query_service(monkeypatch):
    workflow = object()

    async def fake_get_analysis_query_workflow():
        return workflow

    monkeypatch.setattr(
        dependencies,
        "get_analysis_query_workflow",
        fake_get_analysis_query_workflow,
    )

    service = asyncio.run(dependencies.get_analysis_query_service())

    assert isinstance(service, AnalysisQueryService)
    assert service.workflow is workflow


def test_get_analysis_query_controller_returns_analysis_query_controller(
    monkeypatch,
):
    service = object()

    async def fake_get_analysis_query_service():
        return service

    monkeypatch.setattr(
        dependencies,
        "get_analysis_query_service",
        fake_get_analysis_query_service,
    )

    controller = asyncio.run(dependencies.get_analysis_query_controller())

    assert isinstance(controller, AnalysisQueryController)
    assert controller.service is service
