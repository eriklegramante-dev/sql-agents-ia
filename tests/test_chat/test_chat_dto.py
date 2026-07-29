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
            user_id=" user-1 ",
            message="  hello  ",
            session_id=" session-1 ",
        )

        self.assertEqual(request.user_id, "user-1")
        self.assertEqual(request.message, "hello")
        self.assertEqual(request.session_id, "session-1")

    def test_normalizes_empty_session_id_to_none(self):
        request = ChatMessageRequestDTO(
            user_id=1,
            message="hello",
            session_id="   ",
        )

        self.assertIsNone(request.session_id)

    def test_accepts_optional_context_fields(self):
        request = ChatMessageRequestDTO(
            user_id=1,
            message="total sales",
            dataset_id=DATASET_ID,
            metadata={"source": "dashboard"},
        )

        self.assertEqual(request.dataset_id, DATASET_ID)
        self.assertEqual(request.metadata, {"source": "dashboard"})

    def test_rejects_user_id_lower_than_one(self):
        with self.assertRaises(ValidationError):
            ChatMessageRequestDTO(
                user_id=0,
                message="hello",
            )

    def test_rejects_empty_string_user_id(self):
        with self.assertRaises(ValidationError):
            ChatMessageRequestDTO(
                user_id="   ",
                message="hello",
            )

    def test_rejects_empty_message_after_normalization(self):
        with self.assertRaises(ValidationError):
            ChatMessageRequestDTO(
                user_id=1,
                message="   ",
            )

    def test_rejects_extra_fields(self):
        with self.assertRaises(ValidationError):
            ChatMessageRequestDTO(
                user_id=1,
                message="hello",
                unexpected=True,
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
                    content={"kind": "bar"},
                ),
            },
            errors=None,
        )

        self.assertTrue(response.success)
        self.assertEqual(response.data.artifact.type, "chart")
        self.assertEqual(response.data.artifact.content, {"kind": "bar"})


if __name__ == "__main__":
    unittest.main()
