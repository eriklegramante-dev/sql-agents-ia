import pytest
from app.core.read.agent_preferences_workflow import AgentPreferencesWorkflow

class TestAgentPreferencesRead:
    """
    Conjunto de testes unitários para validar o fluxo de leitura
    das preferências do agente através do Workflow.
    """

    def test_retrieval_success_with_existing_preferences(self, mock_repository):
        """
        Cenário: O usuário possui preferências customizadas salvas no banco.
        Esperado: O sistema deve retornar os dados exatos do banco.
        """
        workflow = AgentPreferencesWorkflow(repository=mock_repository)
        
        result = workflow.execute(1)
        
        assert result is not None
        assert result["user_id"] == 1
        assert result["persona_name"] == "Sênior"
        assert result["response_style"] == "direto e técnico"

    def test_fallback_to_default_profile_when_preferences_missing(self, mock_repository):
            """
            Cenário: O usuário existe, mas não possui preferências customizadas salvas.
            Esperado: O sistema deve ativar a Regra de Ouro e retornar o perfil padrão vindo das configurações.
            """
            from app.settings.setting import get_settings
            settings = get_settings()
            
            workflow = AgentPreferencesWorkflow(repository=mock_repository)
            
            result = workflow.execute(99)
            
            assert result is not None
            assert result["user_id"] == 99
            assert result["persona_name"] == settings.agent.default_persona_name  
            assert result["language"] == settings.agent.default_language     
            assert "execute_sql" in result["tool_preferences"]

    @pytest.mark.parametrize("invalid_id", ["abc", -5, 0, None])
    def test_validation_fails_with_invalid_user_id(self, mock_repository, invalid_id):
        """
        Cenário: O formato do user_id fornecido é inválido (letras, negativo, zero ou nulo).
        Esperado: O Workflow deve lançar um ValueError impedindo o avanço do fluxo.
        """
        workflow = AgentPreferencesWorkflow(repository=mock_repository)
        
        with pytest.raises(ValueError) as exc_info:
            workflow.execute(invalid_id)
            
        assert "O identificador do usuário (user_id) fornecido é inválido." in str(exc_info.value)