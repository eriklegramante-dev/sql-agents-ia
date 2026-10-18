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

    async def execute(self, request, *, user_id):
        self.received_request = request
        self.received_user_id = user_id

        if self.exception is not None:
            raise self.exception

        return self.response


class FakeLogger:
    def log_info(self, message):
        pass

    def log_warning(self, message):
        pass

    def log_error(self, message):
        pass


class ChatMessageControllerTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_returns_success_payload(self):
        response_data = ChatMessageResponseDataDTO(
            user_id=37,
            session_id="session-1",
            answer="Hello.",
            intent="general_chat",
            tool_used=None,
            dataset_id=None,
            artifact=None,
        )
        service = FakeChatService(response_data)
        controller = ChatMessageController(service, logger=FakeLogger())
        request = ChatMessageRequestDTO(
            message="hello",
            session_id="session-1",
        )

        result = await controller.execute(request, user_id=37)

        self.assertEqual(service.received_user_id, 37)
        self.assertIs(service.received_request, request)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Chat message processed successfully.")
        self.assertIs(result.data, response_data)
        self.assertIsNone(result.errors)
        self.assertEqual(set(result.model_dump()), {"success", "message", "data", "errors"})
        self.assertIsNone(result.model_extra)

    async def test_execute_translates_app_exception_to_http_exception(self):
        service = FakeChatService(
            exception=ValidationException(
                "Invalid chat message.",
                details=["message is required"],
            )
        )
        controller = ChatMessageController(service, logger=FakeLogger())
        request = ChatMessageRequestDTO(
            message="hello",
        )

        with self.assertRaises(HTTPException) as context:
            await controller.execute(request, user_id=37)

        self.assertEqual(service.received_user_id, 37)
        self.assertIs(service.received_request, request)
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

    async def test_execute_propagates_unexpected_error(self):
        service = FakeChatService(exception=RuntimeError("boom"))
        controller = ChatMessageController(service, logger=FakeLogger())
        request = ChatMessageRequestDTO(
            message="hello",
        )

        with self.assertRaises(RuntimeError) as context:
            await controller.execute(request, user_id=37)

        self.assertEqual(str(context.exception), "boom")


if __name__ == "__main__":
    unittest.main()
