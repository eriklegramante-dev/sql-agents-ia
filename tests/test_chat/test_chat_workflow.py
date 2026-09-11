import unittest

from app.chat.models import ChatArtifact, ChatIntent, ChatMessageInput
from app.core.chat.workflow import ChatMessageWorkflow
from tests.helpers import DATASET_ID


class FakePreferencesWorkflow:
    def __init__(self, preferences=None):
        self.preferences = preferences or {}
        self.received_user_id = None

    async def execute(self, user_id):
        self.received_user_id = user_id
        return self.preferences


class FakeIntentDetector:
    def __init__(self, intent):
        self.intent = intent
        self.received_message = None

    def detect(self, message):
        self.received_message = message
        return self.intent


class FakeAssistant:
    def __init__(self, answer="Assistant answer."):
        self.answer = answer
        self.received_message = None
        self.received_preferences = None

    async def execute(self, message, preferences):
        self.received_message = message
        self.received_preferences = preferences
        return self.answer


class FakeQueryTool:
    def __init__(self):
        self.received_dataset_id = None
        self.received_message = None

    async def execute(self, dataset_id, message):
        self.received_dataset_id = dataset_id
        self.received_message = message
        return ChatArtifact(
            type="query_result",
            content={
                "columns": ["total"],
                "rows": [{"total": 100}],
            },
        )


class FakeChartTool:
    def __init__(self):
        self.received_dataset_id = None
        self.received_message = None

    async def execute(self, dataset_id, message):
        self.received_dataset_id = dataset_id
        self.received_message = message
        return ChatArtifact(
            type="chart",
            content={
                "chart_type": "bar",
                "title": "Sales",
                "labels": ["Jan"],
                "series": [{"name": "sales", "values": [100]}],
            },
        )


class ChatMessageWorkflowTest(unittest.IsolatedAsyncioTestCase):
    def build_workflow(
        self,
        preferences_workflow=None,
        intent_detector=None,
        assistant=None,
        query_tool=None,
        chart_tool=None,
    ):
        return ChatMessageWorkflow(
            preferences_workflow=preferences_workflow or FakePreferencesWorkflow(),
            intent_detector=intent_detector
            or FakeIntentDetector(
                ChatIntent.GENERAL_CHAT,
            ),
            assistant=assistant or FakeAssistant(),
            query_tool=query_tool or FakeQueryTool(),
            chart_tool=chart_tool or FakeChartTool(),
        )

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
        assistant = FakeAssistant("Assistant answer.")
        workflow = self.build_workflow(
            preferences_workflow=preferences_workflow,
            intent_detector=intent_detector,
            assistant=assistant,
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
        self.assertEqual(assistant.received_message, "hello")
        self.assertEqual(assistant.received_preferences.persona_name, "Analyst")
        self.assertEqual(
            assistant.received_preferences.tool_preferences,
            ("sql",),
        )
        self.assertEqual(
            assistant.received_preferences.guardrails,
            ("never invent",),
        )
        self.assertEqual(result.user_id, 7)
        self.assertEqual(result.session_id, "session-1")
        self.assertEqual(result.answer, "Assistant answer.")
        self.assertEqual(result.intent, ChatIntent.GENERAL_CHAT)
        self.assertIsNone(result.tool_used)
        self.assertIsNone(result.dataset_id)
        self.assertIsNone(result.artifact)

    async def test_execute_returns_dataset_question_temporary_answer(self):
        query_tool = FakeQueryTool()
        workflow = self.build_workflow(
            intent_detector=FakeIntentDetector(ChatIntent.DATASET_QUESTION),
            query_tool=query_tool,
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
        self.assertEqual(query_tool.received_dataset_id, DATASET_ID)
        self.assertEqual(query_tool.received_message, "total sales")
        self.assertEqual(
            result.answer,
            "The analytical query was executed successfully.",
        )
        self.assertEqual(result.tool_used, "query")
        self.assertEqual(result.artifact.type, "query_result")

    async def test_execute_returns_chart_request_temporary_answer(self):
        chart_tool = FakeChartTool()
        workflow = self.build_workflow(
            intent_detector=FakeIntentDetector(ChatIntent.CHART_REQUEST),
            chart_tool=chart_tool,
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
        self.assertEqual(chart_tool.received_dataset_id, DATASET_ID)
        self.assertEqual(chart_tool.received_message, "make a chart")
        self.assertEqual(
            result.answer,
            "The requested chart was generated successfully.",
        )
        self.assertEqual(result.tool_used, "chart")
        self.assertEqual(result.artifact.type, "chart")

    async def test_execute_returns_unsupported_temporary_answer(self):
        workflow = self.build_workflow(
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
            "This request is not supported. The current chat can answer "
            "general questions, analyze a selected dataset, and generate "
            "charts.",
        )


if __name__ == "__main__":
    unittest.main()
