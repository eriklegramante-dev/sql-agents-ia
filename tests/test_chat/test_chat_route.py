import asyncio
import json
import unittest

from fastapi import HTTPException

from app.chat.dependencies import get_chat_message_controller
from app.main import app
from tests.helpers import DATASET_ID


class FakeChatController:
    def __init__(self, response=None, exception=None):
        self.response = response
        self.exception = exception
        self.received_request = None

    async def execute(self, request):
        self.received_request = request

        if self.exception is not None:
            raise self.exception

        return self.response


def post(path: str, payload: dict):
    return asyncio.run(
        asyncio.wait_for(
            asgi_request("POST", path, payload),
            timeout=2,
        )
    )


async def asgi_request(method: str, path: str, payload: dict):
    messages = []
    request_sent = False
    body = json.dumps(payload).encode()

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }

    async def receive():
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}

        request_sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)

    response_start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )

    return response_start["status"], json.loads(response_body)


def make_chat_response():
    return {
        "success": True,
        "message": "Chat message processed successfully.",
        "data": {
            "user_id": 1,
            "session_id": "session-1",
            "answer": "Here is the answer.",
            "intent": "dataset_question",
            "tool_used": None,
            "dataset_id": str(DATASET_ID),
            "artifact": None,
        },
        "errors": None,
    }


class ChatMessageRouteTest(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def override_controller(self, controller: FakeChatController):
        async def get_controller():
            return controller

        app.dependency_overrides[get_chat_message_controller] = get_controller

    def test_send_chat_message_returns_success_response(self):
        expected_response = make_chat_response()
        controller = FakeChatController(response=expected_response)
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/chat/message",
            {
                "user_id": 1,
                "message": "total sales",
                "dataset_id": str(DATASET_ID),
                "session_id": "session-1",
                "metadata": {"origin": "test"},
            },
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(response_json, expected_response)
        self.assertEqual(controller.received_request.user_id, 1)
        self.assertEqual(controller.received_request.message, "total sales")
        self.assertEqual(controller.received_request.dataset_id, DATASET_ID)
        self.assertEqual(controller.received_request.session_id, "session-1")
        self.assertEqual(controller.received_request.metadata, {"origin": "test"})

    def test_send_chat_message_rejects_empty_message(self):
        controller = FakeChatController()
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/chat/message",
            {
                "user_id": 1,
                "message": "   ",
            },
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["body", "message"])
        self.assertIsNone(controller.received_request)

    def test_send_chat_message_rejects_invalid_user_id(self):
        controller = FakeChatController()
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/chat/message",
            {
                "user_id": 0,
                "message": "hello",
            },
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["body", "user_id"])
        self.assertIsNone(controller.received_request)

    def test_send_chat_message_rejects_invalid_dataset_id(self):
        controller = FakeChatController()
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/chat/message",
            {
                "user_id": 1,
                "message": "total sales",
                "dataset_id": "not-a-uuid",
            },
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["body", "dataset_id"])
        self.assertIsNone(controller.received_request)

    def test_send_chat_message_returns_controller_http_exception_response(self):
        controller = FakeChatController(
            exception=HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Invalid chat message.",
                    "data": None,
                    "errors": ["message is required"],
                },
            )
        )
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/chat/message",
            {
                "user_id": 1,
                "message": "hello",
            },
        )

        self.assertEqual(status_code, 400)
        self.assertEqual(
            response_json,
            {
                "detail": {
                    "success": False,
                    "message": "Invalid chat message.",
                    "data": None,
                    "errors": ["message is required"],
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
