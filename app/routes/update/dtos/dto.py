from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class GuardrailsDTO(BaseModel):
    """
    Validates the specific guardrail structure for the POC.
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
        """Sanitizes text fields to avoid leading/trailing spaces or empty strings."""
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned if cleaned else None


class UpdatedAgentPreferencesData(BaseModel):
    """Response payload structure representing the final persisted state."""

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
    """Standardized response envelope for the PUT route."""

    success: bool = Field(..., example=True)
    message: str = Field(..., example="Agent preferences successfully updated.")
    data: UpdatedAgentPreferencesData
