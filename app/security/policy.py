from typing import Optional

from app.routes.delete.user.dtos.dto import DeleteUserRequestDTO
from app.models.users_table import UserTable, UserRole
from app.routes.create.admin.dtos.dto import CreateAdminRequestDTO
from app.routes.create.user.dtos.dto import CreateUserRequestDTO
from app.logs.setup_logger import LoggerManager, LOGGER
from app.routes.read.dtos.dto import GetUserRequestDTO


class UserPolicy:
    """
    Class responsible for handling user authorization policies.

    This class defines the access control rules that determine whether a user can perform
    specific operations on user data based on their role and the provided request attributes.

    Attributes:
        logger (LoggerManager): Logger instance for recording debug and info events during policy checks.
    """

    def __init__(self, logger: Optional[LoggerManager] = None) -> None:
        self.logger = logger or LOGGER

    def can_create(
        self,
        request: CreateUserRequestDTO | CreateAdminRequestDTO,
        current_user: UserTable,
    ) -> bool:
        """
        Determines whether the current user is allowed to create users.

        Args:
            request (CreateUserRequestDTO | CreateAdminRequestDTO): DTO containing creation data.
            current_user (UserTable): The user attempting to perform the creation.

        Returns:
            bool: True if the user is authorized to create users, False otherwise.
        """
        self.logger.log_debug(
            f"[policy] validating create permission for {request.__class__.__name__}"
        )
        if current_user.role == UserRole.ADMIN:
            self.logger.log_debug(f"[policy] ADMIN {current_user.id} can create users.")
            return True

        self.logger.log_info(f"[policy] User {current_user.id} denied create access.")
        return False

    def can_view(
        self,
        request: GetUserRequestDTO,
        current_user: UserTable,
    ) -> bool:
        """
        Validates whether the authenticated user is authorized
        to view user data.

        Authorization rules:

        - Administrators can view any user and apply all filters.
        - Standard users can only access their own profile.
        - Standard users are not allowed to use restricted filters
        such as email, cpf, role, status, or country.
        - Standard users may access their own profile by omitting
        the id filter or by explicitly providing their own id.

        Args:
            request (GetUserRequestDTO):
                DTO containing optional user search filters.

            current_user (UserTable):
                Authenticated user requesting access.

        Returns:
            bool:
                True when the read operation is authorized,
                otherwise False.
        """

        self.logger.log_debug(
            f"[policy] validating view permission " f"for user {current_user.id}"
        )

        if current_user.role == UserRole.ADMIN:
            self.logger.log_info(
                f"[policy] ADMIN {current_user.id} " f"authorized to view users."
            )

            return True

        forbidden_filters = [
            request.email,
            request.name,
            request.cpf,
            request.country,
            request.role,
            request.status,
        ]

        has_forbidden_filters = any(value is not None for value in forbidden_filters)

        if has_forbidden_filters:
            self.logger.log_info(
                f"[policy] Access denied for user "
                f"{current_user.id}: forbidden filters."
            )

            return False

        if request.id is None:
            self.logger.log_info(
                f"[policy] User {current_user.id} " f"authorized to view own profile"
            )

            return True

        if request.id == current_user.id:
            self.logger.log_info(
                f"[policy] User {current_user.id} "
                f"authorized to view own profile by id"
            )

            return True

        self.logger.log_info(
            f"[policy] Access denied for user "
            f"{current_user.id}: attempted access "
            f"to user {request.id}."
        )

        return False

    def can_update(self, request: object, current_user: UserTable) -> bool:
        """
        Validate whether the authenticated user is authorized
        to update the requested user profile.

        Applies authorization rules to ensure that users can only
        update their own profile information and prevents
        modification of privileged fields such as role and status.
        The policy denies update attempts targeting other users
        or restricted account attributes.

        Args:
            request (object):
                Request object containing the target user identifiers
                and update payload data.
            current_user (UserTable):
                Authenticated user attempting to perform the update operation.

        Returns:
            bool:
                True when the update operation is authorized,
                otherwise False.
        """
        if current_user.role == UserRole.ADMIN:
            self.logger.log_info(
                f"[policy] ADMIN {current_user.id} authorized update access."
            )
            return True

        if request.id != current_user.id:
            self.logger.log_info(
                f"[policy] user {current_user.id} denied update access."
            )
            return False

        if request.role is not None:
            self.logger.log_info(
                f"[policy] user {current_user.id} attempted role update."
            )
            return False

        if request.status is not None:
            self.logger.log_info(
                f"[policy] user {current_user.id} attempted status update."
            )
            return False

        self.logger.log_info(
            f"[policy] user {current_user.id} authorized to update own profile."
        )

        return True

    def can_delete(
        self,
        request: DeleteUserRequestDTO,
        current_user: UserTable,
    ) -> bool:
        """
        Determines whether the current user can delete a user.

        Allows administrators to delete any user and restricts
        standard users to deleting only their own account using
        id, email, or cpf.

        Args:
            request (DeleteUserRequestDTO): DTO containing the user
                identifier used for deletion.
            current_user (UserTable): Authenticated user requesting
                the delete operation.

        Returns:
            bool: True when the deletion is allowed, otherwise False.
        """
        self.logger.log_debug(
            f"[policy] validating delete permission for {request.__class__.__name__}"
        )

        if current_user.role == UserRole.ADMIN:
            self.logger.log_info(
                f"[policy] ADMIN {current_user.id} allowed delete access."
            )
            return True

        if request.id is not None and request.id == current_user.id:
            self.logger.log_info(
                f"[policy] USER {current_user.id} allowed delete by own id."
            )
            return True

        if request.email is not None and request.email == current_user.email:
            self.logger.log_info(
                f"[policy] USER {current_user.id} allowed delete by own email."
            )
            return True

        if request.cpf is not None and request.cpf == current_user.cpf:
            self.logger.log_info(
                f"[policy] USER {current_user.id} allowed delete by own cpf."
            )
            return True

        self.logger.log_info(f"[policy] USER {current_user.id} denied delete access.")
        return False
