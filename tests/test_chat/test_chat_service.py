import unittest

from app.chat.models import ChatArtifact, ChatIntent, ChatMessageInput, ChatMessageResult
from app.prepare.exceptions import ValidationException
from app.routes.chat.dtos.dto import ChatMessageRequestDTO
from app.routes.chat.services.service import ChatMessageService
from tests.helpers import DATASET_ID


class FakeChatWorkflow:
    def __init__(self, result=None, exception=None):
        self.result = result
        self.exception = exception
        self.received_request = None

    async def execute(self, request):
        self.received_request = request
        if self.exception is not None:
            raise self.exception
        return self.result


class FakeLogger:
    def log_info(self, message):
        pass


class ChatMessageServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_maps_request_to_workflow_input_and_response_dto(self):
        workflow = FakeChatWorkflow(
            ChatMessageResult(
                user_id=1,
                session_id="session-1",
                answer="Here is the chart.",
                intent=ChatIntent.CHART_REQUEST,
                tool_used="chart_tool",
                dataset_id=DATASET_ID,
                artifact=ChatArtifact(
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
            )
        )
        service = ChatMessageService(workflow, logger=FakeLogger())
        request = ChatMessageRequestDTO(
            message="chart sales",
            dataset_id=DATASET_ID,
            session_id="session-1",
            metadata={"origin": "test"},
        )

        response = await service.execute(request, user_id=37)

        self.assertIsInstance(workflow.received_request, ChatMessageInput)
        self.assertEqual(workflow.received_request.user_id, 37)
        self.assertEqual(workflow.received_request.message, "chart sales")
        self.assertEqual(workflow.received_request.dataset_id, DATASET_ID)
        self.assertEqual(workflow.received_request.session_id, "session-1")
        self.assertEqual(workflow.received_request.metadata, {"origin": "test"})
        self.assertEqual(response.user_id, 37)
        self.assertEqual(response.session_id, "session-1")
        self.assertEqual(response.answer, "Here is the chart.")
        self.assertEqual(response.intent, "chart_request")
        self.assertEqual(response.tool_used, "chart_tool")
        self.assertEqual(response.dataset_id, DATASET_ID)
        self.assertEqual(response.artifact.type, "chart")
        self.assertEqual(
            response.artifact.content,
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

    async def test_execute_maps_missing_artifact_to_none(self):
        workflow = FakeChatWorkflow(
            ChatMessageResult(
                user_id="user-1",
                session_id=None,
                answer="Hello.",
                intent=ChatIntent.GENERAL_CHAT,
                tool_used=None,
                dataset_id=None,
                artifact=None,
            )
        )
        service = ChatMessageService(workflow, logger=FakeLogger())
        request = ChatMessageRequestDTO(
            message="hello",
        )

        response = await service.execute(request, user_id=37)

        self.assertIsInstance(workflow.received_request, ChatMessageInput)
        self.assertEqual(workflow.received_request.user_id, 37)
        self.assertIsNone(workflow.received_request.session_id)
        self.assertEqual(response.user_id, 37)
        self.assertEqual(response.intent, "general_chat")
        self.assertIsNone(response.artifact)

    async def test_execute_propagates_workflow_errors(self):
        for error in (
            ValidationException("Invalid chat message.", details=["message is required"]),
            RuntimeError("boom"),
        ):
            with self.subTest(error=type(error).__name__):
                workflow = FakeChatWorkflow(exception=error)
                service = ChatMessageService(workflow, logger=FakeLogger())
                request = ChatMessageRequestDTO(message="hello")
                with self.assertRaises(type(error)) as context:
                    await service.execute(request, user_id=37)
                self.assertIs(context.exception, error)
                self.assertEqual(workflow.received_request.user_id, 37)


if __name__ == "__main__":
    unittest.main()
