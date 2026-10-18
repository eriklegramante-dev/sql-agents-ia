import unittest

from pydantic import ValidationError

from app.routes.chat.dtos.dto import (
    ChatArtifactDTO,
    ChatMessageRequestDTO,
    ChatMessageResponseDTO,
)
from tests.helpers import DATASET_ID


class ChatMessageRequestDTOTest(unittest.TestCase):
    def test_normalizes_message_and_session_id(self):
        request = ChatMessageRequestDTO(
            message="  hello  ",
            session_id=" session-1 ",
        )

        self.assertNotIn("user_id", request.model_dump())
        self.assertEqual(request.message, "hello")
        self.assertEqual(request.session_id, "session-1")

    def test_normalizes_empty_session_id_to_none(self):
        request = ChatMessageRequestDTO(
            message="hello",
            session_id="   ",
        )

        self.assertIsNone(request.session_id)

    def test_accepts_optional_context_fields(self):
        request = ChatMessageRequestDTO(
            message="total sales",
            dataset_id=DATASET_ID,
            metadata={"source": "dashboard"},
        )

        self.assertEqual(request.dataset_id, DATASET_ID)
        self.assertEqual(request.metadata, {"source": "dashboard"})

    def test_rejects_user_id_in_body(self):
        for user_id in (1, 0, -1, "user-1", "   "):
            with self.subTest(user_id=user_id):
                with self.assertRaises(ValidationError) as context:
                    ChatMessageRequestDTO(user_id=user_id, message="hello")
                self.assertEqual(context.exception.errors()[0]["loc"], ("user_id",))
                self.assertEqual(context.exception.errors()[0]["type"], "extra_forbidden")

    def test_rejects_empty_message_after_normalization(self):
        with self.assertRaises(ValidationError) as context:
            ChatMessageRequestDTO(message="   ")
        self.assertEqual(
            [error["loc"] for error in context.exception.errors()], [("message",)]
        )

    def test_rejects_extra_fields(self):
        with self.assertRaises(ValidationError) as context:
            ChatMessageRequestDTO(message="hello", unexpected=True)
        self.assertEqual(
            [(error["loc"], error["type"]) for error in context.exception.errors()],
            [(("unexpected",), "extra_forbidden")],
        )


class ChatMessageResponseDTOTest(unittest.TestCase):
    def test_builds_response_with_artifact(self):
        response = ChatMessageResponseDTO(
            success=True,
            message="Chat message processed successfully.",
            data={
                "user_id": 1,
                "session_id": "session-1",
                "answer": "Done.",
                "intent": "chart_request",
                "tool_used": "chart_tool",
                "dataset_id": DATASET_ID,
                "artifact": ChatArtifactDTO(
                    type="chart",
                    content={
                        "chart_type": "bar",
                        "title": "Sales",
                        "labels": ["Jan"],
                        "series": [
                            {
                                "name": "sales",
                                "values": [100],
                            }
                        ],
                    },
                ),
            },
            errors=None,
        )

        self.assertTrue(response.success)
        self.assertEqual(response.data.user_id, 1)
        self.assertEqual(response.data.artifact.type, "chart")
        self.assertEqual(
            response.data.artifact.content,
            {
                "chart_type": "bar",
                "title": "Sales",
                "labels": ["Jan"],
                "series": [
                    {
                        "name": "sales",
                        "values": [100],
                    }
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
