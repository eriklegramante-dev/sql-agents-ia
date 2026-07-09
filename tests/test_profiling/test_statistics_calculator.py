import unittest

import pandas as pd

from app.routes.profiling.helpers.statistics.statistics_calculator import (
    StatisticsCalculator,
)


class StatisticsCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.calculator = StatisticsCalculator()

    def test_calculate_for_column_returns_numeric_statistics_ignoring_nulls(self):
        series = pd.Series([10, 20, None, 30])

        statistics = self.calculator.calculate_for_column(series)

        self.assertEqual(
            statistics,
            {
                "min": 10.0,
                "max": 30.0,
                "average": 20.0,
                "median": 20.0,
            },
        )

    def test_calculate_for_column_returns_empty_dict_for_text_series(self):
        series = pd.Series(["paid", "pending"])

        statistics = self.calculator.calculate_for_column(series)

        self.assertEqual(statistics, {})

    def test_calculate_for_column_returns_empty_dict_for_all_null_numeric_series(self):
        series = pd.Series([None, None], dtype="float")

        statistics = self.calculator.calculate_for_column(series)

        self.assertEqual(statistics, {})

    def test_calculate_for_dataframe_returns_statistics_for_numeric_columns_only(self):
        dataframe = pd.DataFrame(
            {
                "amount": [10, 20, 30],
                "score": [1.5, 2.5, 3.5],
                "status": ["paid", "pending", "paid"],
            }
        )

        statistics = self.calculator.calculate_for_dataframe(dataframe)

        self.assertEqual(
            statistics,
            {
                "amount": {
                    "min": 10.0,
                    "max": 30.0,
                    "average": 20.0,
                    "median": 20.0,
                },
                "score": {
                    "min": 1.5,
                    "max": 3.5,
                    "average": 2.5,
                    "median": 2.5,
                },
            },
        )

    def test_calculate_for_dataframe_omits_numeric_columns_without_valid_values(self):
        dataframe = pd.DataFrame(
            {
                "empty_numeric": pd.Series([None, None], dtype="float"),
                "status": ["paid", "pending"],
            }
        )

        statistics = self.calculator.calculate_for_dataframe(dataframe)

        self.assertEqual(statistics, {})


if __name__ == "__main__":
    unittest.main()
