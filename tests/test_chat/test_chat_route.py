import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.chat.dependencies import get_chat_message_controller
from app.main import app
from tests.helpers import DATASET_ID
from app.security.security import get_trusted_user_id, verify_signature


TEST_SIGNATURE = "chat-test-signature"
VALID_HEADERS = {"X-Signature": TEST_SIGNATURE, "X-User-Id": "37"}


class FakeChatController:
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


def post(path: str, payload: dict, headers=None):
    return asyncio.run(
        asyncio.wait_for(
            asgi_request(
                "POST", path, payload, VALID_HEADERS if headers is None else headers
            ),
            timeout=2,
        )
    )


async def asgi_request(method: str, path: str, payload: dict, headers: dict):
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

    scope["headers"].extend(
        (name.lower().encode(), value.encode()) for name, value in headers.items()
    )

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
            "user_id": 37,
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
    def setUp(self):
        original_overrides = app.dependency_overrides.copy()

        def restore_overrides():
            app.dependency_overrides.clear()
            app.dependency_overrides.update(original_overrides)

        self.addCleanup(restore_overrides)
        app.dependency_overrides.pop(get_trusted_user_id, None)
        app.dependency_overrides.pop(verify_signature, None)
        settings_patch = patch(
            "app.security.security.get_settings",
            return_value=SimpleNamespace(
                security=SimpleNamespace(secret_key=TEST_SIGNATURE)
            ),
        )
        settings_patch.start()
        self.addCleanup(settings_patch.stop)

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
                "message": "total sales",
                "dataset_id": str(DATASET_ID),
                "session_id": "session-1",
                "metadata": {"origin": "test"},
            },
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(response_json, expected_response)
        self.assertEqual(controller.received_user_id, 37)
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
                "message": "   ",
            },
        )

        self.assertEqual(status_code, 422)
        self.assertEqual(response_json["detail"][0]["loc"], ["body", "message"])
        self.assertIsNone(controller.received_request)

    def test_rejects_missing_or_invalid_security_headers_before_execute(self):
        cases = [
            ({}, "x-signature"),
            ({"X-User-Id": "37"}, "x-signature"),
            ({"X-Signature": TEST_SIGNATURE}, "X-User-Id"),
        ]
        cases.extend(
            ({"X-Signature": TEST_SIGNATURE, "X-User-Id": value}, "X-User-Id")
            for value in ("0", "-1", "abc", "1.5", "")
        )
        for headers, field in cases:
            with self.subTest(headers=headers):
                controller = FakeChatController()
                self.override_controller(controller)
                status_code, response = post(
                    "/api/v1/chat/message", {"message": "hello"}, headers=headers
                )
                self.assertEqual(status_code, 422)
                self.assertIn(
                    ["header", field], [error["loc"] for error in response["detail"]]
                )
                self.assertIsNone(controller.received_request)

    def test_rejects_incorrect_signature_before_execute(self):
        controller = FakeChatController()
        self.override_controller(controller)
        status_code, response = post(
            "/api/v1/chat/message", {"message": "hello"},
            headers={"X-Signature": "wrong-signature", "X-User-Id": "37"},
        )
        self.assertEqual(status_code, 401)
        self.assertEqual(response, {"detail": "Invalid signature"})
        self.assertIsNone(controller.received_request)

    def test_rejects_user_id_in_body_even_with_valid_headers(self):
        for headers in (VALID_HEADERS, {}):
            with self.subTest(headers=headers):
                controller = FakeChatController(response=make_chat_response())
                self.override_controller(controller)
                status_code, response = post(
                    "/api/v1/chat/message", {"message": "hello", "user_id": 1},
                    headers=headers,
                )
                self.assertEqual(status_code, 422)
                self.assertIn(
                    {"loc": ["body", "user_id"], "type": "extra_forbidden"},
                    [{"loc": error["loc"], "type": error["type"]}
                     for error in response["detail"]],
                )
                self.assertIsNone(controller.received_request)

    def test_send_chat_message_rejects_invalid_dataset_id(self):
        controller = FakeChatController()
        self.override_controller(controller)

        status_code, response_json = post(
            "/api/v1/chat/message",
            {
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
