import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import openai

from app.adapters.chat.openai_assistant_executor import (
    execute_openai_assistant,
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

    def build_settings(
        self,
        api_key="test-key",
        model="gpt-5.6-luna",
    ):
        return SimpleNamespace(
            openai=SimpleNamespace(
                api_key=api_key,
                model=model,
            )
        )

    def build_client(self):
        client = MagicMock()
        client.responses.create = AsyncMock()
        return client

    async def test_returns_generated_answer(self):
        settings = self.build_settings()
        client = self.build_client()
        client.responses.create.return_value = SimpleNamespace(
            output_text="  resposta gerada  "
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.get_settings",
                return_value=settings,
            ),
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ) as mocked_openai,
        ):
            result = await execute_openai_assistant(
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
        settings = self.build_settings(api_key="")

        with patch(
            "app.adapters.chat.openai_assistant_executor.get_settings",
            return_value=settings,
        ), self.assertRaises(
            AssistantExecutionException,
        ) as context:
            await execute_openai_assistant(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant service is not configured.",
        )

    async def test_raises_when_response_is_empty(self):
        settings = self.build_settings()
        client = self.build_client()
        client.responses.create.return_value = SimpleNamespace(
            output_text="   "
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.get_settings",
                return_value=settings,
            ),
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),self.assertRaises(
            AssistantExecutionException,
        ) as context
        ):
            await execute_openai_assistant(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant returned an empty response.",
        )

    async def test_translates_authentication_error(self):
        settings = self.build_settings()
        client = self.build_client()
        client.responses.create.side_effect = (
            openai.AuthenticationError(
                "invalid api key",
                response=MagicMock(),
                body=None,
            )
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.get_settings",
                return_value=settings,
            ),
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),self.assertRaises(
            AssistantExecutionException,
        ) as context
        ):
            await execute_openai_assistant(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant service authentication failed.",
        )

    async def test_translates_rate_limit_error(self):
        settings = self.build_settings()
        client = self.build_client()
        client.responses.create.side_effect = openai.RateLimitError(
            "rate limit",
            response=MagicMock(),
            body=None,
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.get_settings",
                return_value=settings,
            ),
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),self.assertRaises(
            AssistantUnavailableException,
        ) as context
        ):
            await execute_openai_assistant(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant service is temporarily busy. Please try again.",
        )

    async def test_translates_timeout_error(self):
        settings = self.build_settings()
        client = self.build_client()
        client.responses.create.side_effect = openai.APITimeoutError(
            request=MagicMock(),
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.get_settings",
                return_value=settings,
            ),
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),self.assertRaises(
            AssistantTimeoutException,
        )
        ):
            await execute_openai_assistant(
                "Olá",
                self.preferences,
            )

    async def test_translates_connection_error(self):
        settings = self.build_settings()
        client = self.build_client()
        client.responses.create.side_effect = openai.APIConnectionError(
            request=MagicMock(),
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.get_settings",
                return_value=settings,
            ),
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),self.assertRaises(
            AssistantUnavailableException,
        ) as context
        ):
            await execute_openai_assistant(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "Unable to reach the assistant service.",
        )

    async def test_translates_api_status_error(self):
        settings = self.build_settings()
        client = self.build_client()
        client.responses.create.side_effect = openai.APIStatusError(
            "status error",
            response=MagicMock(),
            body=None,
        )

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.get_settings",
                return_value=settings,
            ),
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),self.assertRaises(
            AssistantUnavailableException,
        ) as context
        ):
            await execute_openai_assistant(
                "Olá",
                self.preferences,
            )

        self.assertEqual(
            context.exception.message,
            "The assistant service returned an unexpected response.",
        )

    async def test_translates_unexpected_error(self):
        settings = self.build_settings()
        client = self.build_client()
        client.responses.create.side_effect = RuntimeError("boom")

        with (
            patch(
                "app.adapters.chat.openai_assistant_executor.get_settings",
                return_value=settings,
            ),
            patch(
                "app.adapters.chat.openai_assistant_executor.AsyncOpenAI",
                return_value=client,
            ),self.assertRaises(
            AssistantExecutionException,
        )
        ):
            await execute_openai_assistant(
                "Olá",
                self.preferences,
            )


if __name__ == "__main__":
    unittest.main()