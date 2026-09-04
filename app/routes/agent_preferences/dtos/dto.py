from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AgentPreferencesRequest(BaseModel):
    user_id: int

class AgentPreferencesData(BaseModel):
    user_id: int
    persona_name: Optional[str] = None
    persona_description: Optional[str] = None
    response_style: Optional[str] = None
    language: Optional[str] = None
    default_dataset_scope: Optional[str] = None
    tool_preferences: Optional[list] = []
    guardrails: Optional[list] = []
    
class AgentPreferencesResponse(BaseModel):
    success: bool
    message: str
    data: AgentPreferencesData


class UpdateAISettingsDTO(BaseModel):
    """
    Data Transfer Object for updating user AI settings.
    
    Captures partial updates from the frontend interface. All fields are optional 
    to support PATCH-like update behavior.
    """
    apiKey: Optional[str] = Field(
        default=None, 
        description="The raw API key provided by the user. Masked values (e.g., '••••••••') are ignored."
    )
    persona: Optional[str] = Field(
        default=None, 
        description="The selected conversational persona (e.g., 'executive', 'friendly')."
    )
    model: Optional[str] = Field(
        default=None, 
        description="The underlying LLM model identifier (e.g., 'gpt-5')."
    )
    temperature: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=1.0, 
        description="The creativity/randomness threshold for the AI responses, between 0.0 and 1.0."
    )
    responseStyles: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="A dynamic dictionary of specific stylistic toggles for the AI output."
    )

class AISettingsResponse(BaseModel):
    """
    Data Transfer Object for delivering AI settings to the frontend UI.
    
    Ensures secure data transmission by providing a boolean flag for the API key's 
    existence rather than exposing the actual sensitive key value.
    """
    hasApiKey: bool = Field(
        description="Flag indicating if a valid API key is currently stored for the user."
    )
    persona: str = Field(
        description="The active conversational persona."
    )
    model: str = Field(
        description="The active LLM model identifier."
    )
    temperature: float = Field(
        description="The active temperature setting governing response creativity."
    )
    responseStyles: Dict[str, Any] = Field(
        description="The active stylistic toggles applied to AI responses."
    )