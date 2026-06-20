from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class AgentPreferencesData(BaseModel):
    """
    Representa a estrutura interna dos dados de preferência do agente.
    """
    user_id: int = Field(..., description="Identificador único do usuário")
    persona_name: str = Field(..., description="Nome da persona adotada pelo agente de IA")
    persona_description: str = Field(..., description="Descrição detalhada do papel e comportamento da persona")
    response_style: str = Field(..., description="Estilo de escrita do agente (ex: técnico, casual, direto)")
    language: str = Field(default="pt-BR", description="Idioma padrão das respostas")
    default_dataset_scope: Optional[str] = Field(None, description="Escopo ou banco de dados padrão que o agente deve focar")
    tool_preferences: List[str] = Field(default_factory=list, description="Lista de ferramentas permitidas para o agente")
    guardrails: List[str] = Field(default_factory=list, description="Diretrizes e restrições de segurança que o agente deve seguir")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Data de criação do registro")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Data da última atualização do registro")

    class Config:
        from_attributes = True


class AgentPreferencesResponse(BaseModel):
    """
    DTO padrão de resposta exigido pela arquitetura do projeto.
    """
    success: bool = Field(..., description="Indica se a requisição foi processada com sucesso")
    message: str = Field(..., description="Mensagem de feedback sobre a operação")
    data: Optional[AgentPreferencesData] = Field(None, description="Dados das preferências do agente")