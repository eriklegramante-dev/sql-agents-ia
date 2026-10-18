from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.core.analysis.query_count_workflow import QueryCountWorkflow
from app.database.connection import get_db_pool
from app.database.query_execution_repository import QueryExecutionRepository
from app.logs.setup_logger import LOGGER
from app.security.security import get_trusted_user_id


class QueryCountDataDTO(BaseModel):
    """Represent the nonnegative successful execution count.

    Attributes:
        count: Number of execution records stored for the trusted user.
    """
    count: int = Field(ge=0)


class QueryCountResponseDTO(BaseModel):
    """Represent the successful query-count response envelope.

    Attributes:
        success: Indicates successful retrieval of the count.
        message: Human-readable retrieval message.
        data: Successful execution count for the trusted user.
        errors: Optional error details in the response contract.
    """
    success: bool
    message: str
    data: QueryCountDataDTO
    errors: list[str] | None = None


class QueryCountService:
    """Service responsible for mapping query counts to API response data.

    Forwards the trusted user identifier to the workflow and constructs the
    validated count DTO consumed by the controller.

    Attributes:
        workflow:
            Workflow responsible for retrieving the user's stored count.
    """

    def __init__(self, workflow: QueryCountWorkflow) -> None:
        """Initialize the query count service.

        Args:
            workflow:
                Workflow used to retrieve counts for the trusted user.
        """
        self.workflow = workflow

    async def execute(self, *, user_id: int) -> QueryCountDataDTO:
        """Map the trusted user's execution count to response data.

        Args:
            user_id: Trusted user identifier forwarded by the controller.

        Returns:
            Validated response data containing the count.

        Workflow and response validation failures propagate to the controller.
        """
        count = await self.workflow.execute(user_id=user_id)
        return QueryCountDataDTO(count=count)


class QueryCountController:
    """Controller responsible for building query count responses.

    Delegates retrieval to the service and wraps successful counts in the
    standard response envelope. Service failures are logged and translated
    into HTTP 500 responses with Cache-Control set to no-store.

    Attributes:
        service:
            Application service used to retrieve query count response data.
    """

    def __init__(self, service: QueryCountService) -> None:
        """Initialize the query count controller.

        Args:
            service:
                Application service responsible for retrieving query count data.
        """
        self.service = service

    async def execute(self, *, user_id: int) -> QueryCountResponseDTO:
        """Build a count response or translate retrieval failures to HTTP 500.

        Args:
            user_id: Trusted user identifier forwarded by the route.

        Returns:
            Standard response envelope containing the stored count.

        Raises:
            HTTPException: If the service fails, with a no-store error response.
        """
        try:
            data = await self.service.execute(user_id=user_id)
        except Exception as error:
            LOGGER.logger.exception("Failed to retrieve successful query count.")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "message": "Failed to retrieve successful query count.",
                    "data": None,
                    "errors": None,
                },
                headers={"Cache-Control": "no-store"},
            ) from error

        return QueryCountResponseDTO(
            success=True,
            message="Successful query count retrieved.",
            data=data,
        )


async def get_query_count_controller() -> QueryCountController:
    """Compose execution persistence, count workflow, service, and controller.

    Returns:
        Controller backed by the shared PostgreSQL pool.

    Pool creation failures propagate during dependency resolution, before
    controller-level error handling runs.
    """
    pool = await get_db_pool()
    repository = QueryExecutionRepository(pool)
    workflow = QueryCountWorkflow(repository)
    service = QueryCountService(workflow)
    return QueryCountController(service)


router = APIRouter()


@router.get(
    "/queries/count",
    response_model=QueryCountResponseDTO,
)
async def get_query_count(
    response: Response,
    user_id: int = Depends(get_trusted_user_id),
    controller: QueryCountController = Depends(get_query_count_controller),
) -> QueryCountResponseDTO:
    """Retrieve the trusted user's count with a no-store success response.

    Args:
        response: Response receiving the Cache-Control header.
        user_id: Positive identity forwarded with a valid internal signature.
        controller: Injected query-count controller.

    Returns:
        Standardized response containing the user's stored execution count.

    Raises:
        HTTPException: If security validation or controller execution fails.
    """
    response.headers["Cache-Control"] = "no-store"
    return await controller.execute(user_id=user_id)