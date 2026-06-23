from typing import Optional, Dict, Any

class AgentPreferencesRepository:
    """
    Directly responsible for accessing the persisted data of the agent's preferences.
    Isolates the SQL query logic from the rest of the application.
    """

    def find_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Searches for an agent's preferences in the database by user ID.
        Returns a dictionary with the raw data or None if not found.
        """
        return None