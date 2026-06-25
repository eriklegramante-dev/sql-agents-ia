import logging
from datetime import datetime
from uuid import UUID

from app.adapters.storage.base import StorageAdapter
from app.config.settings import settings
from app.prepare.exceptions import ConflictException, NotFoundException, StorageException
from app.database.dataset_repository import DatasetRepository
from app.enums.dataset_status import DatasetStatus
from app.routes.prepare.dtos.dto import DatasetPreparationResponseData
from app.routes.prepare.helpers.dataframe.dataframe_reader import DataFrameReader
from app.routes.prepare.helpers.parquet.parquet_writer import ParquetWriter
from app.routes.prepare.helpers.schema.schema_inferer import SchemaInferer

logger = logging.getLogger(__name__)


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
        self.raw_container = settings.RAW_CONTAINER
        self.prepared_container = settings.PREPARED_CONTAINER

    async def execute(self, dataset_id: UUID) -> DatasetPreparationResponseData:
        """Prepare one completed dataset and return its response payload.

        Args:
            dataset_id (UUID): Identifier of the dataset to prepare.

        Returns:
            DatasetPreparationResponseData: Prepared dataset metadata, row and
            column counts, prepared object key, and inferred schema.

        Raises:
            NotFoundException: If no dataset exists for ``dataset_id``.
            ConflictException: If the dataset is not in completed status.
            StorageException: If the raw file cannot be read from storage.
            Exception: Re-raises unexpected processing or persistence errors
            after marking the dataset as failed.
        """
        dataset = await self.repository.get_by_id(dataset_id)

        if dataset is None:
            raise NotFoundException(f"Dataset with ID {dataset_id} not found")

        if dataset.status != DatasetStatus.COMPLETED:
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

            parquet_data = ParquetWriter.dataframe_to_parquet_bytes(
                processed_dataframe
            )

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

            return DatasetPreparationResponseData(
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
            raise StorageException(str(error))

        except Exception as error:
            await self.repository.update_status(
                dataset_id,
                DatasetStatus.FAILED,
                str(error),
            )
            raise
