import unittest

from fastapi import HTTPException

from app.prepare.exceptions import ValidationException
from app.routes.chat.controllers.controller import ChatMessageController
from app.routes.chat.dtos.dto import (
    ChatMessageRequestDTO,
    ChatMessageResponseDataDTO,
)


class FakeChatService:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_request = None

    async def execute(self, request):
        self.received_request = request

        if self.exception is not None:
            raise self.exception

        return self.response


class ChatMessageControllerTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_returns_success_payload(self):
        response_data = ChatMessageResponseDataDTO(
            user_id=1,
            session_id="session-1",
            answer="Hello.",
            intent="general_chat",
            tool_used=None,
            dataset_id=None,
            artifact=None,
        )
        service = FakeChatService(response_data)
        controller = ChatMessageController(service)
        request = ChatMessageRequestDTO(
            user_id=1,
            message="hello",
            session_id="session-1",
        )

        result = await controller.execute(request)

        self.assertIs(service.received_request, request)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Chat message processed successfully.")
        self.assertIs(result.data, response_data)
        self.assertIsNone(result.errors)

    async def test_execute_translates_app_exception_to_http_exception(self):
        service = FakeChatService(
            exception=ValidationException(
                "Invalid chat message.",
                details=["message is required"],
            )
        )
        controller = ChatMessageController(service)
        request = ChatMessageRequestDTO(
            user_id=1,
            message="hello",
        )

        with self.assertRaises(HTTPException) as context:
            await controller.execute(request)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(
            context.exception.detail,
            {
                "success": False,
                "message": "Invalid chat message.",
                "data": None,
                "errors": ["message is required"],
            },
        )

    async def test_execute_translates_unexpected_error_to_internal_error(self):
        service = FakeChatService(exception=RuntimeError("boom"))
        controller = ChatMessageController(service)
        request = ChatMessageRequestDTO(
            user_id=1,
            message="hello",
        )

        with self.assertRaises(HTTPException) as context:
            await controller.execute(request)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(
            context.exception.detail,
            {
                "success": False,
                "message": (
                    "Internal server error during chat message processing."
                ),
                "data": None,
                "errors": [
                    "An unexpected internal error occurred.",
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
