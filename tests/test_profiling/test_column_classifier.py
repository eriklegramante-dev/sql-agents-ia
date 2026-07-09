import unittest

import pandas as pd

from app.routes.profiling.helpers.column.column_classifier import ColumnClassifier


class ColumnClassifierTest(unittest.TestCase):
    def setUp(self):
        self.classifier = ColumnClassifier()

    def test_classifies_numeric_series(self):
        series = pd.Series([1, 2.5, None])

        result = self.classifier.classify(series)

        self.assertEqual(result, "numeric")

    def test_classifies_boolean_series(self):
        series = pd.Series([True, False, True])

        result = self.classifier.classify(series)

        self.assertEqual(result, "boolean")

    def test_classifies_datetime_series(self):
        series = pd.Series(pd.to_datetime(["2026-06-23", "2026-06-24"]))

        result = self.classifier.classify(series)

        self.assertEqual(result, "datetime")

    def test_classifies_string_series_as_text(self):
        series = pd.Series(["paid", "pending"], dtype="string")

        result = self.classifier.classify(series)

        self.assertEqual(result, "text")

    def test_classifies_object_series_as_text(self):
        series = pd.Series([{"amount": 10}, {"amount": 20}], dtype="object")

        result = self.classifier.classify(series)

        self.assertEqual(result, "text")

    def test_classifies_unsupported_series_as_unknown(self):
        series = pd.Series(pd.Categorical(["small", "large"]))

        result = self.classifier.classify(series)

        self.assertEqual(result, "unknown")


if __name__ == "__main__":
    unittest.main()
