from app.chat.exceptions import (
    AssistantExecutionException,
    ChartGenerationException,
    ChatException,
    QueryExecutionException,
)


def test_chat_exception() -> None:
    exception = ChatException(
        message="Chat error",
        status_code=400,
        error_type="chat_error",
        details=["detail"],
    )

    assert exception.message == "Chat error"
    assert exception.status_code == 400
    assert exception.error_type == "chat_error"
    assert exception.details == ["detail"]


def test_assistant_execution_exception() -> None:
    exception = AssistantExecutionException()

    assert exception.status_code == 500
    assert exception.error_type == "assistant_execution_error"


def test_query_execution_exception() -> None:
    exception = QueryExecutionException()

    assert exception.status_code == 500
    assert exception.error_type == "query_execution_error"


def test_chart_generation_exception() -> None:
    exception = ChartGenerationException()

    assert exception.status_code == 500
    assert exception.error_type == "chart_generation_error"
