import openai
from openai import AsyncOpenAI

from app.adapters.chat.assistant_adapter import AssistantExecutor
from app.chat.exceptions import (
    AssistantExecutionException,
    AssistantTimeoutException,
    AssistantUnavailableException,
)
from app.chat.models import ChatPreferences


def create_openai_assistant_executor(
    api_key: str,
    model: str,
) -> AssistantExecutor:
    """
    Create a configured OpenAI assistant executor.

    The OpenAI configuration is provided explicitly by the application
    composition layer instead of being resolved from global settings inside
    the adapter.

    Args:
        api_key:
            OpenAI API key used to authenticate requests.

        model:
            OpenAI model used to generate assistant responses.

    Returns:
        AssistantExecutor:
            Configured asynchronous executor compatible with
            AssistantAdapter.
    """

    async def execute_openai_assistant(
        message: str,
        preferences: ChatPreferences,
    ) -> str:
        """
        Generate a conversational response using the OpenAI API.

        Args:
            message:
                User message submitted to the assistant.

            preferences:
                Effective chat preferences used to configure assistant
                behavior.

        Returns:
            str:
                Generated assistant response.

        Raises:
            AssistantExecutionException:
                If configuration, authentication, or response validation
                fails.

            AssistantUnavailableException:
                If the OpenAI service cannot currently process the request.

            AssistantTimeoutException:
                If the OpenAI request takes too long.
        """
        if not api_key:
            raise AssistantExecutionException(
                "The assistant service is not configured."
            )

        client = AsyncOpenAI(
            api_key=api_key,
            timeout=30.0,
        )

        instructions = (
            f"You are {preferences.persona_name}. "
            f"{preferences.persona_description} "
            f"Respond in {preferences.language}. "
            f"Use a {preferences.response_style} response style."
        )

        try:
            response = await client.responses.create(
                model=model,
                instructions=instructions,
                input=message,
            )

        except openai.AuthenticationError as error:
            raise AssistantExecutionException(
                "The assistant service authentication failed."
            ) from error

        except openai.RateLimitError as error:
            raise AssistantUnavailableException(
                "The assistant service is temporarily busy. Please try again."
            ) from error

        except openai.APITimeoutError as error:
            raise AssistantTimeoutException() from error

        except openai.APIConnectionError as error:
            raise AssistantUnavailableException(
                "Unable to reach the assistant service."
            ) from error

        except openai.APIStatusError as error:
            raise AssistantUnavailableException(
                "The assistant service returned an unexpected response."
            ) from error

        except openai.APIError as error:
            raise AssistantExecutionException() from error

        except Exception as error:
            raise AssistantExecutionException() from error

        answer = response.output_text.strip()

        if not answer:
            raise AssistantExecutionException(
                "The assistant returned an empty response."
            )

        return answer

    return execute_openai_assistant