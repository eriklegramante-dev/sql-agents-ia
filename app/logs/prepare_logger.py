from app.logs.setup_logger import LOGGER


class PrepareLogger:
    """Centralizes standardized logs for the dataset preparation flow."""

    @staticmethod
    def started(dataset_id: str) -> None:
        LOGGER.log_info(
            f"[prepare] Starting dataset preparation: dataset_id={dataset_id}"
        )

    @staticmethod
    def status_updated_to_preparing(dataset_id: str) -> None:
        LOGGER.log_debug(
            f"[prepare] Dataset status updated to preparing: dataset_id={dataset_id}"
        )

    @staticmethod
    def raw_file_read(dataset_id: str, raw_object_key: str) -> None:
        LOGGER.log_debug(
            "[prepare] Raw dataset file read from storage: "
            f"dataset_id={dataset_id}, raw_object_key={raw_object_key}"
        )

    @staticmethod
    def schema_inferred(dataset_id: str, rows_count: int, columns_count: int) -> None:
        LOGGER.log_debug(
            "[prepare] Dataset schema inferred: "
            f"dataset_id={dataset_id}, rows_count={rows_count}, columns_count={columns_count}"
        )

    @staticmethod
    def prepared_file_written(dataset_id: str, prepared_object_key: str) -> None:
        LOGGER.log_debug(
            "[prepare] Prepared dataset file written to storage: "
            f"dataset_id={dataset_id}, prepared_object_key={prepared_object_key}"
        )

    @staticmethod
    def prepared_successfully(dataset_id: str, prepared_object_key: str) -> None:
        LOGGER.log_info(
            "[prepare] Dataset prepared successfully: "
            f"dataset_id={dataset_id}, prepared_object_key={prepared_object_key}"
        )

    @staticmethod
    def dataset_not_found(dataset_id: str) -> None:
        LOGGER.log_warning(f"[prepare] Dataset not found: dataset_id={dataset_id}")

    @staticmethod
    def preparation_rejected(dataset_id: str, status: str) -> None:
        LOGGER.log_warning(
            f"[prepare] Dataset preparation rejected: dataset_id={dataset_id}, status={status}"
        )

    @staticmethod
    def raw_file_not_found(dataset_id: str, error: str) -> None:
        LOGGER.log_error(
            f"[prepare] Raw dataset file not found during preparation: "
            f"dataset_id={dataset_id}, error={error}"
        )

    @staticmethod
    def failed(dataset_id: str, error: str) -> None:
        LOGGER.log_error(
            f"[prepare] Dataset preparation failed: dataset_id={dataset_id}, error={error}"
        )

    @staticmethod
    def succeeded(dataset_id: str, prepared_object_key: str) -> None:
        PrepareLogger.prepared_successfully(dataset_id, prepared_object_key)

    @staticmethod
    def not_found(dataset_id: str) -> None:
        PrepareLogger.dataset_not_found(dataset_id)
