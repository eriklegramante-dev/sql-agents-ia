import unittest

import pandas as pd

from app.routes.profiling.helpers.quality.quality_checker import QualityChecker


class QualityCheckerTest(unittest.TestCase):
    def setUp(self):
        self.checker = QualityChecker()

    def test_check_returns_empty_list_when_dataframe_has_no_quality_warnings(self):
        dataframe = pd.DataFrame(
            {
                "amount": [10, 20, 10, 30],
                "status": ["paid", "pending", "paid", "failed"],
            }
        )

        warnings = self.checker.check(dataframe)

        self.assertEqual(warnings, [])

    def test_check_warns_for_high_null_percentage(self):
        dataframe = pd.DataFrame({"mostly_null": [None, None, None, None, 10]})

        warnings = self.checker.check(dataframe)

        self.assertIn(
            "Column 'mostly_null' has a high null percentage.",
            warnings,
        )

    def test_check_warns_for_empty_column(self):
        dataframe = pd.DataFrame({"empty": [None, None, None]})

        warnings = self.checker.check(dataframe)

        self.assertIn("Column 'empty' is empty.", warnings)

    def test_check_warns_for_suspiciously_high_cardinality(self):
        dataframe = pd.DataFrame({"identifier": ["a", "b", "c"]})

        warnings = self.checker.check(dataframe)

        self.assertIn(
            "Column 'identifier' has suspiciously high cardinality.",
            warnings,
        )

    def test_check_warns_for_single_distinct_value(self):
        dataframe = pd.DataFrame({"constant": ["same", "same", "same"]})

        warnings = self.checker.check(dataframe)

        self.assertIn(
            "Column 'constant' contains only one distinct value.",
            warnings,
        )

    def test_calculate_percentage_returns_zero_when_total_is_zero(self):
        percentage = self.checker._calculate_percentage(10, 0)

        self.assertEqual(percentage, 0.0)

    def test_calculate_percentage_rounds_to_two_decimal_places(self):
        percentage = self.checker._calculate_percentage(1, 3)

        self.assertEqual(percentage, 33.33)


if __name__ == "__main__":
    unittest.main()
