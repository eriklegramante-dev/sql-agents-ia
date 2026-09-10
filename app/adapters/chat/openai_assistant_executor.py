import openai
from openai import AsyncOpenAI

from app.chat.exceptions import (
    AssistantExecutionException,
    AssistantTimeoutException,
    AssistantUnavailableException,
)
from app.chat.models import ChatPreferences
from app.settings.setting import get_settings


async def execute_openai_assistant(
    message: str,
    preferences: ChatPreferences,
) -> str:
    """
    Generates a conversational response using the OpenAI API.

    Args:
        message:
            User message submitted to the assistant.

        preferences:
            Effective chat preferences used to configure assistant behavior.

    Returns:
        str:
            Generated assistant response.

    Raises:
        AssistantExecutionException:
            If configuration, authentication, or response validation fails.

        AssistantUnavailableException:
            If the OpenAI service cannot currently process the request.

        AssistantTimeoutException:
            If the OpenAI request takes too long.
    """
    settings = get_settings()

    if not settings.openai.api_key:
        raise AssistantExecutionException(
            "The assistant service is not configured."
        )

    client = AsyncOpenAI(
        api_key=settings.openai.api_key,
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
            model=settings.openai.model,
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