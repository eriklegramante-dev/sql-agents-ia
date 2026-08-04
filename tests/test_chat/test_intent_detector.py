import unittest

from app.chat.intent_detector import ChatIntentDetector
from app.chat.models import ChatIntent


class ChatIntentDetectorTest(unittest.TestCase):
    def setUp(self):
        self.detector = ChatIntentDetector()

    def test_detects_unsupported_intent_before_other_keywords(self):
        intent = self.detector.detect("Drop table sales and show total")

        self.assertEqual(intent, ChatIntent.UNSUPPORTED)

    def test_detects_chart_request(self):
        intent = self.detector.detect("Create a bar chart for sales")

        self.assertEqual(intent, ChatIntent.CHART_REQUEST)

    def test_detects_dataset_question(self):
        intent = self.detector.detect("What is the average sales total?")

        self.assertEqual(intent, ChatIntent.DATASET_QUESTION)

    def test_detects_general_chat_when_no_keywords_match(self):
        intent = self.detector.detect("Hello, can you help me?")

        self.assertEqual(intent, ChatIntent.GENERAL_CHAT)

    def test_detects_portuguese_keywords(self):
        intent = self.detector.detect("Qual e a soma de vendas da tabela?")

        self.assertEqual(intent, ChatIntent.DATASET_QUESTION)


if __name__ == "__main__":
    unittest.main()
