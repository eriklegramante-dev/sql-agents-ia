from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import HTTPException, status


class AgentPreferencesUpdateWorkflow:
    """
    Core workflow engine responsible for the business logic of updating agent preferences.

    Coordinates transactional validation, enforces safe default configurations from the POC
    on creation (Scenario A), and manages data merging to preserve omitted fields during
    partial profile updates (Scenario B).

    Attributes:
        repository (Any): The data persistence layer component handling storage operations.
    """

    def __init__(self, repository: Any = None) -> None:
        """
        Initializes the workflow with optional repository injection.

        Args:
            repository (Any, optional): The database repository instance. Defaults to None.
        """
        self.repository = repository

    def execute(self, user_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the business logic for creating or updating agent preferences (Upsert).
        Ensures safe defaults for new configurations and preserves omitted fields for existing ones.

        Args:
            user_id (int): The unique identifier of the user. Must be a positive integer.
            update_data (Dict[str, Any]): Dictionary containing the fields to update or create.

        Returns:
            Dict[str, Any]: The finalized state of the agent preferences after execution.

        Raises:
            HTTPException: 400 Bad Request if user_id is non-positive or if update_data payload is empty.
        """
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user identifier. ID must be a positive integer.",
            )

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty update payload. At least one configurable preference field must be provided.",
            )

        current_time = datetime.now(timezone.utc)

        existing_preferences = None
        if self.repository:
            existing_preferences = self.repository.get_by_user_id(user_id)

        if not existing_preferences:
            final_preferences = {
                "user_id": user_id,
                "persona_name": update_data.get("persona_name", "AI SQL Assistant"),
                "persona_description": update_data.get(
                    "persona_description", "Standard data assistant persona."
                ),
                "response_style": update_data.get("response_style", "concise"),
                "language": update_data.get("language", "en"),
                "default_dataset_scope": update_data.get("default_dataset_scope", {}),
                "tool_preferences": update_data.get("tool_preferences", {}),
                "guardrails": update_data.get(
                    "guardrails",
                    {
                        "allow_sql_generation": True,
                        "allow_chart_generation": True,
                        "allow_dataset_mutation": False,
                        "max_rows_to_preview": 100,
                    },
                ),
                "created_at": current_time,
                "updated_at": current_time,
            }
        else:
            final_preferences = {
                "user_id": user_id,
                "persona_name": update_data.get(
                    "persona_name", existing_preferences["persona_name"]
                ),
                "persona_description": update_data.get(
                    "persona_description",
                    existing_preferences.get("persona_description"),
                ),
                "response_style": update_data.get(
                    "response_style", existing_preferences["response_style"]
                ),
                "language": update_data.get(
                    "language", existing_preferences["language"]
                ),
                "default_dataset_scope": update_data.get(
                    "default_dataset_scope",
                    existing_preferences.get("default_dataset_scope"),
                ),
                "tool_preferences": update_data.get(
                    "tool_preferences", existing_preferences.get("tool_preferences", {})
                ),
                "guardrails": update_data.get(
                    "guardrails", existing_preferences.get("guardrails", {})
                ),
                "created_at": existing_preferences["created_at"],
                "updated_at": current_time,
            }

        if self.repository:
            self.repository.upsert(user_id, final_preferences)

        return final_preferences
