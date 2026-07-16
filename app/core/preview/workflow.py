from typing import Any, Optional
from uuid import UUID

from app.adapters.storage.local_storage_adapter import LocalStorageAdapter
from app.database.dataset_repository import DatasetRepository
from app.enums.dataset_status import DatasetStatus
from app.logs.setup_logger import LOGGER, LoggerManager
from app.prepare.exceptions import AppException
from app.routes.preview.dtos.dto import (
    DatasetPreviewRequestDTO,
    DatasetPreviewResponseDataDTO,
)
from app.routes.preview.helpers.preview_reader import PreviewReader


class DatasetPreviewWorkflow:
    """
    Coordinates dataset preview retrieval.

    This workflow validates the dataset, loads the prepared Parquet file,
    generates a limited and serializable preview, and assembles the response
    payload returned by the service layer.

    Attributes:
        dataset_repository:
            Repository used to retrieve dataset metadata.
        storage_adapter:
            Adapter used to load prepared dataset files.
        preview_reader:
            Helper used to read and serialize Parquet previews.
        logger:
            Logger manager used during workflow execution.
    """

    DEFAULT_LIMIT: int = 20
    MAXIMUM_LIMIT: int = 100
    PREPARED_CONTAINER: str = "prepared"

    def __init__(
        self,
        dataset_repository: DatasetRepository,
        storage_adapter: LocalStorageAdapter,
        preview_reader: PreviewReader,
        logger: LoggerManager | None = None
    ) -> None: 
        self.dataset_repository = dataset_repository
        self.storage_adapter = storage_adapter
        self.preview_reader = preview_reader 
        self.logger = logger or LOGGER

    async def execute(
        self,
        request: DatasetPreviewRequestDTO,
    ) -> DatasetPreviewResponseDataDTO:
        self._validate_dependencies()

        normalized_limit = self._normalize_limit(request.limit)

        self.logger.log_info(
            f"Starting dataset preview retrieval for dataset "
            f"{request.dataset_id}."
        )

        dataset = await self.dataset_repository.get_by_id(
            request.dataset_id,
        )

        self._validate_dataset_exists(
            dataset=dataset,
            dataset_id=request.dataset_id,
        )
        self._validate_dataset_status(dataset.status)
        self._validate_prepared_object_key(
            dataset.prepared_object_key,
        )

        parquet_content = await self.storage_adapter.read_file(
            container=self.PREPARED_CONTAINER,
            path=dataset.prepared_object_key,
        )

        preview_result = self.preview_reader.read(
            parquet_content,
            normalized_limit,
        )

        rows_count = self._resolve_rows_count(
            persisted_rows_count=dataset.rows_count,
            parquet_rows_count=preview_result.rows_count,
        )

        response_data = DatasetPreviewResponseDataDTO(
            dataset_id=request.dataset_id,
            status=self._extract_status_value(dataset.status),
            limit=normalized_limit,
            columns=preview_result.columns,
            rows=preview_result.rows,
            rows_count=rows_count,
            returned_rows_count=len(preview_result.rows),
        )

        self.logger.log_info(
            f"Dataset preview retrieved successfully for dataset "
            f"{request.dataset_id}."
        )

        return response_data

    def _validate_dependencies(self) -> None:
        if self.dataset_repository is None:
            raise RuntimeError(
                "Dataset repository dependency was not configured."
            )

        if self.storage_adapter is None:
            raise RuntimeError(
                "Storage adapter dependency was not configured."
            )

        if self.preview_reader is None:
            raise RuntimeError(
                "Preview reader dependency was not configured."
            )

    def _normalize_limit(
        self,
        limit: int | None,
    ) -> int:
        if limit is None:
            return self.DEFAULT_LIMIT

        if limit <= 0:
            raise AppException(
                message="Preview limit must be greater than zero.",
                status_code=422,
            )

        return min(limit, self.MAXIMUM_LIMIT)

    def _validate_dataset_exists(
        self,
        dataset: Any,
        dataset_id: UUID,
    ) -> None:
        if dataset is None:
            raise AppException(
                message=f"Dataset {dataset_id} was not found.",
                status_code=404,
            )

    def _validate_dataset_status(
        self,
        dataset_status: DatasetStatus | str,
    ) -> None:
        normalized_status = self._extract_status_value(dataset_status)

        allowed_statuses = {
            DatasetStatus.PREPARED.value,
        }

        if hasattr(DatasetStatus, "PROFILED"):
            allowed_statuses.add(DatasetStatus.PROFILED.value)

        if normalized_status not in allowed_statuses:
            raise AppException(
                message=(
                    "Dataset must be prepared or profiled before preview "
                    "retrieval."
                ),
                status_code=409,
            )

    def _validate_prepared_object_key(
        self,
        prepared_object_key: str | None,
    ) -> None:
        if not prepared_object_key:
            raise AppException(
                message=(
                    "Dataset does not have a prepared object available."
                ),
                status_code=409,
            )

    def _extract_status_value(
        self,
        dataset_status: DatasetStatus | str,
    ) -> str:
        if isinstance(dataset_status, DatasetStatus):
            return dataset_status.value

        return dataset_status

    def _resolve_rows_count(
        self,
        persisted_rows_count: int | None,
        parquet_rows_count: int,
    ) -> int:
        if persisted_rows_count is not None:
            return persisted_rows_count

        return parquet_rows_count
