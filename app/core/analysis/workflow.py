from typing import Any
from uuid import UUID

from app.core.analysis.contracts import (
    AnalysisDatasetRepository,
    AnalysisQueryExecutor,
    SQLValidator,
)
from app.adapters.storage.base import StorageAdapter
from app.enums.dataset_status import DatasetStatus
from app.logs.setup_logger import LoggerManager
from app.prepare.exceptions import AppException
from app.core.analysis.models import (
    AnalysisQueryInput,
    AnalysisQueryOutput,
)


class AnalysisQueryWorkflow:
    """
    Coordinates safe analytical query execution against prepared datasets.

    This workflow validates the requested dataset, ensures that it is ready
    for analysis, loads its prepared Parquet representation, validates the
    provided SQL query, applies a safe row limit, delegates query execution
    to the analytical adapter, and assembles the structured response data.

    Direct SQL queries are prioritized when both SQL and a natural-language
    question are provided. Natural-language SQL generation is intentionally
    not implemented in this initial proof-of-concept flow.

    All infrastructure dependencies are received through constructor
    injection. The workflow does not instantiate repositories, storage
    implementations, validators, or query adapters.

    Attributes:
        dataset_repository:
            Repository responsible for retrieving dataset metadata.

        storage_adapter:
            Storage abstraction responsible for loading prepared dataset
            objects.

        sql_validator:
            Validator responsible for ensuring that only safe read-only SQL
            queries are executed.

        query_adapter:
            Adapter responsible for executing validated analytical queries
            against prepared Parquet content.

        logger:
            Logger manager used during workflow execution.
    """

    DEFAULT_LIMIT: int = 20
    MAXIMUM_LIMIT: int = 100
    PREPARED_CONTAINER: str = "prepared"

    def __init__(
        self,
        dataset_repository: AnalysisDatasetRepository,
        storage_adapter: StorageAdapter,
        sql_validator: SQLValidator,
        query_adapter: AnalysisQueryExecutor,
        logger: LoggerManager,
    ) -> None:
        self.dataset_repository = dataset_repository
        self.storage_adapter = storage_adapter
        self.sql_validator = sql_validator
        self.query_adapter = query_adapter
        self.logger = logger

    async def execute(
        self,
        request: AnalysisQueryInput,
    ) -> AnalysisQueryOutput:
        """
        Execute a safe analytical query against a prepared dataset.

        Args:
            request:
                Validated analysis query request containing the dataset
                identifier, optional natural-language question, optional
                direct SQL query, and requested row limit.

        Returns:
            AnalysisQueryResponseDataDTO:
                Structured analytical result containing the executed SQL,
                returned columns, rows, row counts, and applied limit.

        Raises:
            AppException:
                If the dataset does not exist, is not ready for analysis,
                has no prepared object, no executable SQL is available, or
                the provided SQL query is unsafe.

        """

        normalized_limit = self._normalize_limit(request.limit)

        self.logger.log_info(
            f"Starting analysis query for dataset {request.dataset_id}."
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

        sql = self._resolve_sql(request)

        safe_sql = self._validate_sql(sql)

        query_result = self.query_adapter.execute(
            parquet_content=parquet_content,
            sql=safe_sql,
            limit=normalized_limit,
        )

        response_data = AnalysisQueryOutput(
            dataset_id=request.dataset_id,
            executed_sql=safe_sql,
            columns=query_result.columns,
            rows=query_result.rows,
            rows_count=query_result.rows_count,
            returned_rows_count=query_result.returned_rows_count,
            limit=normalized_limit,
        )

        self.logger.log_info(
            f"Analysis query completed successfully for dataset "
            f"{request.dataset_id}."
        )

        return response_data

    def _normalize_limit(
        self,
        limit: int | None,
    ) -> int:
        """
        Normalize the requested row limit.

        Args:
            limit:
                Requested maximum number of rows.

        Returns:
            int:
                Safe normalized row limit.

        Raises:
            AppException:
                If the provided limit is less than or equal to zero.
        """
        if limit is None:
            return self.DEFAULT_LIMIT

        if limit <= 0:
            raise AppException(
                message="Analysis query limit must be greater than zero.",
                status_code=422,
            )

        return min(limit, self.MAXIMUM_LIMIT)

    def _validate_dataset_exists(
        self,
        dataset: Any,
        dataset_id: UUID,
    ) -> None:
        """
        Ensure the requested dataset exists.

        Args:
            dataset:
                Dataset metadata returned by the repository.

            dataset_id:
                Identifier of the requested dataset.

        Raises:
            AppException:
                If no dataset was found.
        """
        if dataset is None:
            raise AppException(
                message=f"Dataset {dataset_id} was not found.",
                status_code=404,
            )

    def _validate_dataset_status(
        self,
        dataset_status: DatasetStatus | str,
    ) -> None:
        """
        Ensure the dataset is ready for analytical queries.

        Args:
            dataset_status:
                Current dataset processing status.

        Raises:
            AppException:
                If the dataset has not been prepared or profiled.
        """
        normalized_status = self._extract_status_value(
            dataset_status,
        )

        allowed_statuses = {
            DatasetStatus.PREPARED.value,
        }

        if hasattr(DatasetStatus, "PROFILED"):
            allowed_statuses.add(
                DatasetStatus.PROFILED.value,
            )

        if normalized_status not in allowed_statuses:
            raise AppException(
                message=(
                    "Dataset must be prepared or profiled before analysis."
                ),
                status_code=409,
            )

    def _validate_prepared_object_key(
        self,
        prepared_object_key: str | None,
    ) -> None:
        """
        Ensure the dataset has a prepared Parquet object.

        Args:
            prepared_object_key:
                Storage object key associated with the prepared dataset.

        Raises:
            AppException:
                If no prepared object is available.
        """
        if not prepared_object_key:
            raise AppException(
                message=(
                    "Dataset does not have a prepared object available."
                ),
                status_code=409,
            )

    def _resolve_sql(
        self,
        request: AnalysisQueryInput,
    ) -> str:
        """
        Resolve the SQL query that should be executed.

        Direct SQL takes priority when both SQL and a natural-language
        question are provided.

        Natural-language SQL generation is not available in the initial
        proof-of-concept implementation.

        Args:
            request:
                Validated analysis query request.

        Returns:
            str:
                Direct SQL query selected for execution.

        Raises:
            AppException:
                If only a natural-language question is provided.
        """
        if request.sql is not None:
            return request.sql

        if request.question is not None:
            raise AppException(
                message=(
                    "Natural-language query generation is not available yet. "
                    "Provide a direct SQL query for analysis."
                ),
                status_code=422,
            )

        raise AppException(
            message=(
                "At least one of 'question' or 'sql' must be provided."
            ),
            status_code=422,
        )

    def _validate_sql(
        self,
        sql: str,
    ) -> str:
        """
        Validate the SQL query before analytical execution.

        Args:
            sql:
                SQL query selected for execution.

        Returns:
            str:
                Normalized and validated read-only SQL query.

        Raises:
            AppException:
                If the SQL query fails safety validation.
        """
        try:
            return self.sql_validator.validate(sql)

        except ValueError as error:
            raise AppException(
                message=str(error),
                status_code=422,
            ) from error

    def _extract_status_value(
        self,
        dataset_status: DatasetStatus | str,
    ) -> str:
        """
        Extract a comparable dataset status value.

        Args:
            dataset_status:
                Dataset status represented either as an enum or string.

        Returns:
            str:
                Normalized status value.
        """
        if isinstance(dataset_status, DatasetStatus):
            return dataset_status.value

        return dataset_status