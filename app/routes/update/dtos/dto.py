from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class GuardrailsDTO(BaseModel):
    """
    Validates the specific guardrail structure for the POC.

    Attributes:
        allow_sql_generation (bool): Permit AI to generate SQL queries. Defaults to True.
        allow_chart_generation (bool): Permit AI to generate visual charts. Defaults to True.
        allow_dataset_mutation (bool): Permit AI to mutate the datasets. Defaults to False.
        max_rows_to_preview (int): Maximum row previews allowed. Must be greater than 0. Defaults to 100.
    """

    allow_sql_generation: bool = Field(
        True, description="Permit AI to generate SQL queries."
    )
    allow_chart_generation: bool = Field(
        True, description="Permit AI to generate visual charts."
    )
    allow_dataset_mutation: bool = Field(
        False, description="Permit AI to mutate the datasets."
    )
    max_rows_to_preview: int = Field(
        100, gt=0, description="Maximum row previews allowed."
    )

    model_config = {"extra": "forbid"}


class AgentPreferencesUpdateRequest(BaseModel):
    """
    Contract for updating or creating agent preferences (PUT Payload).
    Strictly avoids prompt injections, arbitrary secrets, or extra fields.

    Attributes:
        persona_name (Optional[str]): Customized name for the AI agent (2 to 50 characters).
        persona_description (Optional[str]): Purpose and behavior details (5 to 500 characters).
        response_style (Optional[Literal]): Tone enforcement selection.
        language (Optional[str]): Localized output language code (2 to 10 characters).
        default_dataset_scope (Optional[Dict[str, Any]]): Data workspace restrictions.
        tool_preferences (Optional[Dict[str, Any]]): Feature enablement flags.
        guardrails (Optional[GuardrailsDTO]): Embedded safety boundary configurations.
        metadata (Optional[Dict[str, Any]]): Auxiliary system parameters.
    """

    persona_name: Optional[str] = Field(None, min_length=2, max_length=50)
    persona_description: Optional[str] = Field(None, min_length=5, max_length=500)
    response_style: Optional[
        Literal["concise", "detailed", "technical", "business"]
    ] = Field(None)
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    default_dataset_scope: Optional[Dict[str, Any]] = Field(None)
    tool_preferences: Optional[Dict[str, Any]] = Field(None)
    guardrails: Optional[GuardrailsDTO] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)

    model_config = {"extra": "forbid"}

    @field_validator("persona_name", "persona_description", "language")
    @classmethod
    def sanitize_strings(cls, value: Optional[str]) -> Optional[str]:
        """
        Sanitizes text fields to avoid leading/trailing spaces or empty strings.

        Args:
            value (Optional[str]): The incoming raw text string value from the request.

        Returns:
            Optional[str]: The whitespace-trimmed string, or None if the resulting text is empty.
        """
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned if cleaned else None


class UpdatedAgentPreferencesData(BaseModel):
    """
    Response payload structure representing the final persisted state.

    Attributes:
        user_id (int): Identifier linking the preferences back to the explicit owner.
        persona_name (str): Active identifier name of the AI configuration profile.
        persona_description (Optional[str]): Informative summary text describing system persona.
        response_style (str): Output style constraint currently applied.
        language (str): Communication language active for the agent interface.
        default_dataset_scope (Optional[Dict[str, Any]]): Restricted environment boundary configurations.
        tool_preferences (Dict[str, Any]): Active tool integrations dictionary.
        guardrails (Dict[str, Any]): Hard validation rules compiled for the workspace.
        created_at (datetime): Persistent timestamp marking creation sequence.
        updated_at (datetime): Persistent timestamp marking latest modification event.
    """

    user_id: int
    persona_name: str
    persona_description: Optional[str] = None
    response_style: str
    language: str
    default_dataset_scope: Optional[Dict[str, Any]] = None
    tool_preferences: Dict[str, Any]
    guardrails: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AgentPreferencesUpdateResponse(BaseModel):
    """
    Standardized response envelope for the PUT route.

    Attributes:
        success (bool): Execution tracking indicator status.
        message (str): Plain-text feedback communication targeted for consumer confirmation logs.
        data (UpdatedAgentPreferencesData): Embedded data object wrapping the internal record changes.
    """

    success: bool = Field(..., example=True)
    message: str = Field(..., example="Agent preferences successfully updated.")
    data: UpdatedAgentPreferencesData
