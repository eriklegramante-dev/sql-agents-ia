from datetime import datetime
from uuid import UUID

from app.adapters.storage.base import StorageAdapter
from app.database.dataset_repository import DatasetRepository
from app.enums.dataset_status import DatasetStatus
from app.logs.prepare_logger import PrepareLogger
from app.prepare.exceptions import (
    ConflictException,
    NotFoundException,
    StorageException,
)
from app.routes.prepare.dtos.dto import DatasetPreparationDataDTO
from app.routes.prepare.helpers.dataframe.dataframe_reader import DataFrameReader
from app.routes.prepare.helpers.parquet.parquet_writer import ParquetWriter
from app.routes.prepare.helpers.schema.schema_inferer import SchemaInferer
from app.settings.setting import get_settings


class DatasetPreparationWorkflow:
    """Orchestrates the full dataset preparation flow.

    Validates dataset state, reads raw storage, normalizes and infers schema,
    writes prepared Parquet output, persists schema metadata, and updates status
    transitions on success or failure.

    Args:
        dataset_repository (DatasetRepository): Repository used to read dataset
            records, persist schema metadata, and update preparation status.
        storage_adapter (StorageAdapter): Storage adapter used to read raw files
            and write prepared Parquet files.

    Attributes:
        repository (DatasetRepository): Dataset persistence dependency.
        storage (StorageAdapter): Raw and prepared file storage dependency.
        raw_container (str): Container name used to read uploaded files.
        prepared_container (str): Container name used to write prepared files.
    """

    def __init__(
        self,
        dataset_repository: DatasetRepository,
        storage_adapter: StorageAdapter,
    ):
        self.repository = dataset_repository
        self.storage = storage_adapter
        settings = get_settings()
        self.raw_container = settings.storage.raw_container
        self.prepared_container = settings.storage.prepared_container

    async def execute(self, dataset_id: UUID, *, user_id: int) -> DatasetPreparationDataDTO:
        """Prepare one completed dataset and return its response payload.

        Args:
            user_id: Trusted caller identity required to match the dataset owner.
            dataset_id (UUID): Identifier of the dataset to prepare.

        Returns:
            DatasetPreparationDataDTO: Prepared dataset metadata, row and
            column counts, prepared object key, and inferred schema.

        Raises:
            NotFoundException: If the dataset is missing or not owned by the caller.
            ConflictException: If the dataset is not in completed status.
            StorageException: If the raw file cannot be read from storage.
            Exception: Re-raises unexpected processing or persistence errors
                after marking the dataset as failed.
        """

        PrepareLogger.started(dataset_id)

        dataset = await self.repository.get_by_id(dataset_id)

        if dataset is None or dataset.user_id is None or dataset.user_id != user_id:
            PrepareLogger.not_found(dataset_id)
            raise NotFoundException(f"Dataset with ID {dataset_id} not found")

        if dataset.status != DatasetStatus.COMPLETED:
            PrepareLogger.preparation_rejected(dataset_id, dataset.status.value)
            raise ConflictException(
                f"Dataset cannot be prepared while status is {dataset.status.value}"
            )

        await self.repository.update_status(dataset_id, DatasetStatus.PREPARING)

        prepared_object_key = (
            f"{dataset.id}/prepared_"
            f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.parquet"
        )

        try:
            raw_data = await self.storage.read_file(
                self.raw_container,
                dataset.raw_object_key,
            )

            dataframe = DataFrameReader.read_file(raw_data, dataset.raw_object_key)

            processed_dataframe, columns_schema, rows_count, columns_count = (
                SchemaInferer.process_dataframe(dataframe)
            )

            parquet_data = ParquetWriter.dataframe_to_parquet_bytes(processed_dataframe)

            await self.storage.write_file(
                self.prepared_container,
                prepared_object_key,
                parquet_data,
            )

            await self.repository.save_schema(dataset_id, columns_schema)

            updated_dataset = await self.repository.update_prepared_info(
                dataset_id=dataset_id,
                prepared_object_key=prepared_object_key,
                rows_count=rows_count,
                columns_count=columns_count,
            )
            PrepareLogger.prepared_successfully(dataset_id, prepared_object_key)

            return DatasetPreparationDataDTO(
                dataset_id=updated_dataset.id,
                status=updated_dataset.status.value,
                raw_object_key=updated_dataset.raw_object_key,
                prepared_object_key=updated_dataset.prepared_object_key,
                rows_count=updated_dataset.rows_count,
                columns_count=updated_dataset.columns_count,
                columns_schema=columns_schema,
                updated_at=updated_dataset.updated_at,
            )

        except FileNotFoundError as error:
            await self.repository.update_status(
                dataset_id,
                DatasetStatus.FAILED,
                str(error),
            )
            PrepareLogger.raw_file_not_found(dataset_id, error)
            raise StorageException(str(error))

        except Exception as error:
            await self.repository.update_status(
                dataset_id,
                DatasetStatus.FAILED,
                str(error),
            )
            PrepareLogger.failed(dataset_id, error)
            raise
