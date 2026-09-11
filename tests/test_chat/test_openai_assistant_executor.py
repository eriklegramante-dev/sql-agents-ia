import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import openai

from app.adapters.chat.openai_assistant_executor import (
    create_openai_assistant_executor,
)
from app.chat.exceptions import (
    AssistantExecutionException,
    AssistantTimeoutException,
    AssistantUnavailableException,
)
from app.chat.models import ChatPreferences


class OpenAIAssistantExecutorTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.preferences = ChatPreferences(
            persona_name="SQL Assistant",
            persona_description="Assistant specialized in SQL.",
            response_style="direct",
            language="pt-BR",
            tool_preferences=(),
            guardrails=(),
        )

    def build_client(self):
        client = MagicMock()
        client.responses.create = AsyncMock()
        return client

    async def test_returns_generated_answer(self):
        client = self.build_client()

        client.responses.create.return_value = SimpleNamespace(
            output_text="  resposta gerada  "
        )

        executor = create_openai_assistant_executor(
            api_key="test-key",
            model="gpt-5.6-luna",
        )

        with patch(
            "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
            return_value=client,
        ) as mocked_openai:
            result = await executor(
                "Olá",
                self.preferences,
            )

        self.assertEqual(result, "resposta gerada")

        mocked_openai.assert_called_once_with(
            api_key="test-key",
            timeout=30.0,
        )

        client.responses.create.assert_awaited_once_with(
            model="gpt-5.6-luna",
            instructions=(
                "You are SQL Assistant. "
                "Assistant specialized in SQL. "
                "Respond in pt-BR. "
                "Use a direct response style."
            ),
            input="Olá",
        )

    async def test_raises_when_api_key_is_missing(self):
        executor = create_openai_assistant_executor(
            api_key="",
            model="gpt-5.6-luna",
        )

        with self.assertRaises(
            AssistantExecutionException,
        ) as context:
            await executor(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant service is not configured.",
        )

    async def test_raises_when_response_is_empty(self):
        client = self.build_client()

        client.responses.create.return_value = SimpleNamespace(
            output_text="   "
        )

        executor = create_openai_assistant_executor(
            api_key="test-key",
            model="gpt-5.6-luna",
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),
            self.assertRaises(
                AssistantExecutionException,
            ) as context,
        ):
            await executor(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant returned an empty response.",
        )

    async def test_translates_authentication_error(self):
        client = self.build_client()

        client.responses.create.side_effect = openai.AuthenticationError(
            "invalid api key",
            response=MagicMock(),
            body=None,
        )

        executor = create_openai_assistant_executor(
            api_key="test-key",
            model="gpt-5.6-luna",
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),
            self.assertRaises(
                AssistantExecutionException,
            ) as context,
        ):
            await executor(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant service authentication failed.",
        )

    async def test_translates_rate_limit_error(self):
        client = self.build_client()

        client.responses.create.side_effect = openai.RateLimitError(
            "rate limit",
            response=MagicMock(),
            body=None,
        )

        executor = create_openai_assistant_executor(
            api_key="test-key",
            model="gpt-5.6-luna",
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),
            self.assertRaises(
                AssistantUnavailableException,
            ) as context,
        ):
            await executor(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant service is temporarily busy. Please try again.",
        )

    async def test_translates_timeout_error(self):
        client = self.build_client()

        client.responses.create.side_effect = openai.APITimeoutError(
            request=MagicMock(),
        )

        executor = create_openai_assistant_executor(
            api_key="test-key",
            model="gpt-5.6-luna",
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),
            self.assertRaises(
                AssistantTimeoutException,
            ),
        ):
            await executor(
                "Olá",
                self.preferences,
            )

    async def test_translates_connection_error(self):
        client = self.build_client()

        client.responses.create.side_effect = openai.APIConnectionError(
            request=MagicMock(),
        )

        executor = create_openai_assistant_executor(
            api_key="test-key",
            model="gpt-5.6-luna",
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),
            self.assertRaises(
                AssistantUnavailableException,
            ) as context,
        ):
            await executor(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "Unable to reach the assistant service.",
        )

    async def test_translates_api_status_error(self):
        client = self.build_client()

        client.responses.create.side_effect = openai.APIStatusError(
            "status error",
            response=MagicMock(),
            body=None,
        )

        executor = create_openai_assistant_executor(
            api_key="test-key",
            model="gpt-5.6-luna",
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),
            self.assertRaises(
                AssistantUnavailableException,
            ) as context,
        ):
            await executor(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant service returned an unexpected response.",
        )

    async def test_translates_api_error(self):
        client = self.build_client()

        client.responses.create.side_effect = openai.APIError(
            "api error",
            request=MagicMock(),
            body=None,
        )

        executor = create_openai_assistant_executor(
            api_key="test-key",
            model="gpt-5.6-luna",
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),
            self.assertRaises(
                AssistantExecutionException,
            ),
        ):
            await executor(
                "Olá",
                self.preferences,
            )

    async def test_translates_unexpected_error(self):
        client = self.build_client()

        client.responses.create.side_effect = RuntimeError(
            "boom"
        )

        executor = create_openai_assistant_executor(
            api_key="test-key",
            model="gpt-5.6-luna",
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),
            self.assertRaises(
                AssistantExecutionException,
            ),
        ):
            await executor(
                "Olá",
                self.preferences,
            )


if __name__ == "__main__":
    unittest.main()