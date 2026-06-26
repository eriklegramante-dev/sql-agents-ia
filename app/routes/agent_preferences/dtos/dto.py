from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, timezone
from typing import List, Optional


class AgentPreferencesRequest(BaseModel):
    """
    DTO handling robust validation and sanitization for agent preference read requests.
    """

    user_id: int = Field(
        ...,
        gt=0,
        description="The unique integer identifier of the user to look up preferences.",
    )

    language_filter: Optional[str] = Field(
        None,
        min_length=2,
        max_length=10,
        description="Optional filter to search preferences by language code (e.g., pt-BR).",
    )

    @field_validator("language_filter")
    @classmethod
    def sanitize_language_filter(cls, value: Optional[str]) -> Optional[str]:
        """
        Sanitizes the language filter input by stripping spaces and normalizing cases.
        """
        if value is None:
            return value

        cleaned_value = value.strip()
        if not cleaned_value:
            return None

        return cleaned_value

    model_config = ConfigDict(extra="forbid")


class AgentPreferencesData(BaseModel):
    """
    Represents the internal schema validation for the agent preference core data.
    """

    user_id: int = Field(
        ..., gt=0, description="The unique integer identifier of the user."
    )

    persona_name: str = Field(
        ...,
        min_length=1,
        description="The name of the persona adopted by the AI agent.",
    )
    persona_description: str = Field(
        ...,
        min_length=1,
        description="Detailed profile role and behavioral description of the persona.",
    )
    response_style: str = Field(
        ...,
        min_length=1,
        description="The communication tone and writing style (e.g., technical, direct).",
    )

    language: str = Field(
        default="pt-BR", min_length=2, description="The default response language code."
    )
    default_dataset_scope: Optional[str] = Field(
        None, description="The default secure database scope boundaries for queries."
    )

    tool_preferences: List[str] = Field(
        default_factory=list,
        description="List of functional tools and capabilities permitted for execution.",
    )
    guardrails: List[str] = Field(
        default_factory=list,
        description="Security constraint guidelines and compliance filters applied to the model context.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp indicating when the preference record was initially persisted.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp tracking the most recent modification of the preference record.",
    )

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AgentPreferencesResponse(BaseModel):
    """
    Standard enveloped response DTO ensuring API contract uniformity across the project.
    """

    success: bool = Field(
        ...,
        description="Indicates whether the inbound operation was processed successfully.",
    )
    message: str = Field(
        ...,
        description="Structural context feedback message explaining the operation outcome.",
    )
    data: Optional[AgentPreferencesData] = Field(
        None, description="The validated payload containing agent preference records."
    )

    model_config = ConfigDict(extra="forbid")
