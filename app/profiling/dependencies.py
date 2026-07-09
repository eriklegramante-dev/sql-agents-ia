from app.core.profiling.workflow import DatasetProfileWorkflow
from app.prepare.dependencies import get_dataset_repository, get_storage_adapter
from app.routes.profiling.controllers.controller import DatasetProfileController
from app.routes.profiling.helpers.calculator.profile_calculator import ProfileCalculator
from app.routes.profiling.services.service import DatasetProfileService


async def get_dataset_profile_controller() -> DatasetProfileController:
    """
    Build the dataset profiling controller dependency.

    Wires the profiling controller with its service, workflow, repository,
    storage adapter, and profile calculator dependencies following the project
    architecture.

    Returns:
        DatasetProfileController:
            Controller instance ready to handle dataset profiling requests.
    """
    repository = await get_dataset_repository()
    storage = await get_storage_adapter()

    profile_calculator = ProfileCalculator()
    workflow = DatasetProfileWorkflow(
        repository=repository,
        storage_adapter=storage,
        profile_calculator=profile_calculator,
    )
    service = DatasetProfileService(workflow)

    return DatasetProfileController(service)