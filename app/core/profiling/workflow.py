from datetime import datetime
from io import BytesIO
from typing import Optional
from uuid import UUID

import pandas as pd

from app.adapters.storage.base import StorageAdapter
from app.database.dataset_repository import DatasetRepository
from app.enums.dataset_status import DatasetStatus
from app.logs.setup_logger import LOGGER, LoggerManager
from app.prepare.exceptions import (
    ConflictException,
    NotFoundException,
    ProcessingException,
)
from app.routes.profiling.dtos.dto import (
    DatasetProfileResponseDTO,
    DatasetProfileResponseDataDTO,
)
from app.routes.profiling.helpers.calculator.profile_calculator import ProfileCalculator
from app.settings.setting import get_settings


class DatasetProfileWorkflow:
    """
    Workflow responsible for coordinating dataset profiling.

    This workflow owns the business rules for profiling a prepared dataset. It
    validates whether the dataset exists, ensures that the dataset is eligible
    for profiling, loads the prepared Parquet file through the storage adapter,
    delegates profile calculation to helper classes, persists the generated
    profile metadata, updates the dataset status, and returns the standardized
    response DTO.

    The workflow does not contain HTTP-specific behavior and does not perform
    profiling calculations directly.

    Args:
        repository:
            Repository responsible for dataset persistence operations.
        storage_adapter:
            Adapter responsible for loading prepared dataset files.
        profile_calculator:
            Helper responsible for calculating profiling metadata.
        logger:
            Logger manager used to record workflow events.

    Attributes:
        repository:
            Repository used to access dataset metadata.
        storage_adapter:
            Storage adapter used to load prepared datasets.
        profile_calculator:
            Helper responsible for generating profiling metadata.
        logger:
            Logger used to record workflow execution.
        prepared_container:
            Storage container where prepared datasets are stored.

    """

    def __init__(
        self,
        repository: Optional[DatasetRepository] = None,
        storage_adapter: Optional[StorageAdapter] = None,
        profile_calculator: Optional[ProfileCalculator] = None,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        self.repository = repository
        self.storage_adapter = storage_adapter
        self.profile_calculator = profile_calculator or ProfileCalculator()
        self.logger = (logger or LOGGER).logger

        settings = get_settings()
        self.prepared_container = settings.storage.prepared_container

    async def execute(self, dataset_id: UUID, *, user_id: int) -> DatasetProfileResponseDTO:
        """
        Execute the dataset profiling process.

        Args:
            user_id: Trusted caller identity required to match the dataset owner.
            dataset_id:
                Unique identifier of the dataset to profile.

        Returns:
            DatasetProfileResponseDTO:
                Standardized response containing the generated profile.

        Raises:
            NotFoundException:
                When the dataset does not exist or is not owned by the caller.
            ConflictException:
                When the dataset is not prepared or has no prepared object key.
            ProcessingException:
                When an unexpected profiling failure occurs.
        """
        self.logger.info("Starting dataset profiling.")

        dataset = await self.repository.get_by_id(dataset_id)

        if dataset is None or dataset.user_id is None or dataset.user_id != user_id:
            raise NotFoundException("Dataset not found.")

        if dataset.status != DatasetStatus.PREPARED.value:
            raise ConflictException("Only prepared datasets can be profiled.")

        if not dataset.prepared_object_key:
            raise ConflictException("Prepared dataset object key not found.")

        try:
            await self.repository.update_status(dataset_id, DatasetStatus.PROFILING)

            prepared_bytes = await self.storage_adapter.read_file(
                self.prepared_container,
                dataset.prepared_object_key,
            )

            dataframe = pd.read_parquet(BytesIO(prepared_bytes))

            profile = self.profile_calculator.calculate(dataframe)

            await self.repository.save_profile(
                dataset_id=dataset_id,
                profile=profile,
            )

            await self.repository.update_status(
                dataset_id,
                DatasetStatus.PROFILED,
            )

            return self._build_response(
                dataset_id=dataset_id,
                status=DatasetStatus.PROFILED.value,
                profile=profile,
                updated_at=datetime.utcnow().isoformat(),
            )

        except Exception as error:
            await self.repository.update_status(
                dataset_id,
                DatasetStatus.FAILED,
                str(error),
            )
            self.logger.error("Dataset profiling failed.")
            raise ProcessingException(f"Dataset profiling failed: {error}") from error

    def _build_response(
        self,
        dataset_id: UUID,
        status: str,
        profile: dict,
        updated_at: str,
    ) -> DatasetProfileResponseDTO:
        """
        Build the standardized dataset profile response.

        Args:
            dataset_id:
                Unique identifier of the profiled dataset.
            status:
                Final dataset status after profiling.
            profile:
                Generated profiling metadata.
            updated_at:
                Timestamp of the latest dataset update.

        Returns:
            DatasetProfileResponseDTO:
                Standardized response containing the generated profile.
        """
        return DatasetProfileResponseDTO(
            success=True,
            message="Dataset profiled successfully.",
            data=DatasetProfileResponseDataDTO(
                dataset_id=dataset_id,
                status=status,
                rows_count=profile["rows_count"],
                columns_count=profile["columns_count"],
                columns=profile["columns"],
                nulls_summary=profile["nulls_summary"],
                cardinality_summary=profile["cardinality_summary"],
                basic_statistics=profile["basic_statistics"],
                quality_warnings=profile["quality_warnings"],
                updated_at=updated_at,
            ),
        )
