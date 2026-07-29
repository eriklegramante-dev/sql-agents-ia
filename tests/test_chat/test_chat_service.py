import unittest

from app.chat.models import ChatArtifact, ChatIntent, ChatMessageResult
from app.routes.chat.dtos.dto import ChatMessageRequestDTO
from app.routes.chat.services.service import ChatMessageService
from tests.helpers import DATASET_ID


class FakeChatWorkflow:
    def __init__(self, result):
        self.result = result
        self.received_request = None

    async def execute(self, request):
        self.received_request = request
        return self.result


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
                    content={"kind": "bar"},
                ),
            )
        )
        service = ChatMessageService(workflow)
        request = ChatMessageRequestDTO(
            user_id=1,
            message="chart sales",
            dataset_id=DATASET_ID,
            session_id="session-1",
            metadata={"origin": "test"},
        )

        response = await service.execute(request)

        self.assertEqual(workflow.received_request.user_id, 1)
        self.assertEqual(workflow.received_request.message, "chart sales")
        self.assertEqual(workflow.received_request.dataset_id, DATASET_ID)
        self.assertEqual(workflow.received_request.session_id, "session-1")
        self.assertEqual(workflow.received_request.metadata, {"origin": "test"})
        self.assertEqual(response.user_id, 1)
        self.assertEqual(response.session_id, "session-1")
        self.assertEqual(response.answer, "Here is the chart.")
        self.assertEqual(response.intent, "chart_request")
        self.assertEqual(response.tool_used, "chart_tool")
        self.assertEqual(response.dataset_id, DATASET_ID)
        self.assertEqual(response.artifact.type, "chart")
        self.assertEqual(response.artifact.content, {"kind": "bar"})

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
        service = ChatMessageService(workflow)
        request = ChatMessageRequestDTO(
            user_id="user-1",
            message="hello",
        )

        response = await service.execute(request)

        self.assertEqual(response.intent, "general_chat")
        self.assertIsNone(response.artifact)


if __name__ == "__main__":
    unittest.main()
