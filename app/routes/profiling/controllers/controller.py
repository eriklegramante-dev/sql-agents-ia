from typing import Optional
from uuid import UUID

from app.logs.setup_logger import LOGGER, LoggerManager
from app.routes.profiling.dtos.dto import (
    DatasetProfileRequestDTO,
    DatasetProfileResponseDTO,
)
from app.routes.profiling.services.service import DatasetProfileService


class DatasetProfileController:
    """
    Coordinates dataset profiling requests.

    This controller receives the dataset identifier from the route, validates
    it through the request DTO, delegates execution to the service layer, and
    returns the standardized response DTO.

    The controller does not contain profiling calculations, database access,
    storage logic, or HTTP exception handling.

    Args:
        service:
            Service responsible for executing the dataset profiling use case.
        logger:
            Logger manager used to record controller events.

    Attributes:
        service:
            Application service responsible for coordinating the profiling
            workflow.
        logger:
            Logger used to record controller execution events.

    """

    def __init__(
        self,
        service: Optional[DatasetProfileService] = None,
        logger: Optional[LoggerManager] = None,
    ) -> None:
        self.service = service or DatasetProfileService()
        self.logger = (logger or LOGGER).logger

    async def profile_dataset(self, dataset_id: UUID, *, user_id: int) -> DatasetProfileResponseDTO:
        """
        Process a dataset profiling request.

        Args:
            user_id: Trusted caller identity used to authorize dataset ownership.
            dataset_id:
                Unique identifier of the dataset to profile.

        Returns:
            DatasetProfileResponseDTO:
                Standardized response containing the generated profile.
        """
        self.logger.info("Received dataset profiling request.")

        request = DatasetProfileRequestDTO(dataset_id=dataset_id)

        return await self.service.profile_dataset(request.dataset_id, user_id=user_id)
