import unittest

from app.chat.models import ChatIntent, ChatMessageInput
from app.core.chat.workflow import ChatMessageWorkflow
from tests.helpers import DATASET_ID


class FakePreferencesWorkflow:
    def __init__(self, preferences=None):
        self.preferences = preferences or {}
        self.received_user_id = None

    def execute(self, user_id):
        self.received_user_id = user_id
        return self.preferences


class FakeIntentDetector:
    def __init__(self, intent):
        self.intent = intent
        self.received_message = None

    def detect(self, message):
        self.received_message = message
        return self.intent


class ChatMessageWorkflowTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_returns_general_chat_answer_with_preferences(self):
        preferences_workflow = FakePreferencesWorkflow(
            preferences={
                "persona_name": "Analyst",
                "persona_description": "Data assistant",
                "response_style": "direct",
                "language": "pt-BR",
                "tool_preferences": ["sql", 10],
                "guardrails": ["never invent", None],
            }
        )
        intent_detector = FakeIntentDetector(ChatIntent.GENERAL_CHAT)
        workflow = ChatMessageWorkflow(
            preferences_workflow=preferences_workflow,
            intent_detector=intent_detector,
        )
        request = ChatMessageInput(
            user_id=7,
            message="hello",
            dataset_id=None,
            session_id="session-1",
            metadata={"origin": "test"},
        )

        result = await workflow.execute(request)

        self.assertEqual(preferences_workflow.received_user_id, 7)
        self.assertEqual(intent_detector.received_message, "hello")
        self.assertEqual(result.user_id, 7)
        self.assertEqual(result.session_id, "session-1")
        self.assertEqual(result.answer, "Analyst received your message: hello")
        self.assertEqual(result.intent, ChatIntent.GENERAL_CHAT)
        self.assertIsNone(result.tool_used)
        self.assertIsNone(result.dataset_id)
        self.assertIsNone(result.artifact)

    async def test_execute_returns_dataset_question_temporary_answer(self):
        workflow = ChatMessageWorkflow(
            preferences_workflow=FakePreferencesWorkflow(),
            intent_detector=FakeIntentDetector(ChatIntent.DATASET_QUESTION),
        )
        request = ChatMessageInput(
            user_id="user-1",
            message="total sales",
            dataset_id=DATASET_ID,
            session_id=None,
            metadata=None,
        )

        result = await workflow.execute(request)

        self.assertEqual(result.intent, ChatIntent.DATASET_QUESTION)
        self.assertEqual(result.dataset_id, DATASET_ID)
        self.assertEqual(
            result.answer,
            "The dataset question was identified and will be processed "
            "using the analytical query tool.",
        )

    async def test_execute_returns_chart_request_temporary_answer(self):
        workflow = ChatMessageWorkflow(
            preferences_workflow=FakePreferencesWorkflow(),
            intent_detector=FakeIntentDetector(ChatIntent.CHART_REQUEST),
        )
        request = ChatMessageInput(
            user_id=1,
            message="make a chart",
            dataset_id=DATASET_ID,
            session_id=None,
            metadata=None,
        )

        result = await workflow.execute(request)

        self.assertEqual(result.intent, ChatIntent.CHART_REQUEST)
        self.assertEqual(
            result.answer,
            "The chart request was identified and will be processed "
            "using the chart generation tool.",
        )

    async def test_execute_returns_unsupported_temporary_answer(self):
        workflow = ChatMessageWorkflow(
            preferences_workflow=FakePreferencesWorkflow(),
            intent_detector=FakeIntentDetector(ChatIntent.UNSUPPORTED),
        )
        request = ChatMessageInput(
            user_id=1,
            message="drop database",
            dataset_id=None,
            session_id=None,
            metadata=None,
        )

        result = await workflow.execute(request)

        self.assertEqual(result.intent, ChatIntent.UNSUPPORTED)
        self.assertEqual(
            result.answer,
            "This request is not supported by the assistant.",
        )


if __name__ == "__main__":
    unittest.main()
