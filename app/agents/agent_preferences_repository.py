from typing import Optional, Dict, Any

class AgentPreferencesRepository:
    """
    Responsável direta pelo acesso aos dados persistidos das preferências do agente.
    Isola a lógica de queries SQL do restante da aplicação.
    """

    def find_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca as preferências de um agente no banco de dados pelo ID do usuário.
        Retorna um dicionário com os dados brutos ou None se não encontrar.
        """
        return None