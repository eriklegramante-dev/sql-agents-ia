from app.chat.models import ChatIntent


class ChatIntentDetector:
    """Detects the intent of an incoming chat message."""

    DATASET_KEYWORDS = {
        "average",
        "count",
        "data",
        "dataset",
        "maximum",
        "mean",
        "minimum",
        "rows",
        "sales",
        "sum",
        "table",
        "total",
        "média",
        "dados",
        "dataset",
        "máximo",
        "mínimo",
        "linhas",
        "vendas",
        "soma",
        "tabela",
        "total",
    }

    CHART_KEYWORDS = {
        "bar chart",
        "chart",
        "graph",
        "line chart",
        "pie chart",
        "plot",
        "visualization",
        "visualize",
        "gráfico",
        "pizza",
        "visualização",
        "visualize",
    }

    UNSUPPORTED_KEYWORDS = {
        "delete database",
        "drop database",
        "drop table",
        "remove database",
        "apagar banco",
        "deletar banco",
        "excluir banco",
    }

    def detect(self, message: str) -> ChatIntent:
        """
        Classifies an incoming chat message into one of the supported chat
        intents.

        The message is normalized and compared against the configured keyword
        groups to determine whether it represents a general conversation,
        dataset-related question, chart request, or unsupported operation.

        Args:
            message:
                User message to be analyzed.

        Returns:
            ChatIntent:
                Classification result used by the chat workflow to select the
                appropriate processing path.
        """
        normalized_message = message.casefold().strip()

        if self._contains_keyword(
            message=normalized_message,
            keywords=self.UNSUPPORTED_KEYWORDS,
        ):
            return ChatIntent.UNSUPPORTED

        if self._contains_keyword(
            message=normalized_message,
            keywords=self.CHART_KEYWORDS,
        ):
            return ChatIntent.CHART_REQUEST

        if self._contains_keyword(
            message=normalized_message,
            keywords=self.DATASET_KEYWORDS,
        ):
            return ChatIntent.DATASET_QUESTION

        return ChatIntent.GENERAL_CHAT

    def _contains_keyword(
        self,
        message: str,
        keywords: set[str],
    ) -> bool:
        """
        Checks whether the provided message contains any configured keyword.

        Performs a substring comparison between the normalized message and the
        supplied keyword collection.

        Args:
            message:
                Normalized message to be evaluated.

            keywords:
                Set of keywords associated with a specific chat intent.

        Returns:
            bool:
                True when at least one keyword is found in the message;
                otherwise False.
        """
        return any(keyword in message for keyword in keywords)
