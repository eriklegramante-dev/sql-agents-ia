import unittest

import pandas as pd

from app.routes.profiling.helpers.calculator.profile_calculator import (
    ProfileCalculator,
)


class StubColumnClassifier:
    def classify(self, series):
        if series.name == "amount":
            return "numeric"
        return "text"


class StubStatisticsCalculator:
    def calculate_for_column(self, series):
        if series.name == "amount":
            return {"min": 10.0}
        return {}

    def calculate_for_dataframe(self, dataframe):
        return {"amount": {"min": 10.0}}


class StubQualityChecker:
    def check(self, dataframe):
        return ["quality warning"]


class ProfileCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.calculator = ProfileCalculator(
            column_classifier=StubColumnClassifier(),
            statistics_calculator=StubStatisticsCalculator(),
            quality_checker=StubQualityChecker(),
        )

    def test_calculate_returns_complete_profile(self):
        dataframe = pd.DataFrame(
            {
                "amount": [10, 20, None],
                "status": ["paid", "paid", "pending"],
            }
        )

        profile = self.calculator.calculate(dataframe)

        self.assertEqual(profile["rows_count"], 3)
        self.assertEqual(profile["columns_count"], 2)
        self.assertEqual(profile["basic_statistics"], {"amount": {"min": 10.0}})
        self.assertEqual(profile["quality_warnings"], ["quality warning"])
        self.assertEqual(
            profile["nulls_summary"],
            {
                "total_nulls": 1,
                "columns_with_nulls": 1,
            },
        )
        self.assertEqual(
            profile["cardinality_summary"],
            {
                "high_cardinality_columns": [],
                "low_cardinality_columns": [],
            },
        )
        self.assertEqual(
            profile["columns"],
            [
                {
                    "name": "amount",
                    "type": "numeric",
                    "nullable": True,
                    "null_count": 1,
                    "null_percentage": 33.33,
                    "cardinality": 2,
                    "statistics": {"min": 10.0},
                },
                {
                    "name": "status",
                    "type": "text",
                    "nullable": False,
                    "null_count": 0,
                    "null_percentage": 0.0,
                    "cardinality": 2,
                    "statistics": {},
                },
            ],
        )

    def test_calculate_marks_high_and_low_cardinality_columns(self):
        dataframe = pd.DataFrame(
            {
                "identifier": ["a", "b", "c", "d"],
                "constant": ["same", "same", "same", "same"],
            }
        )

        profile = self.calculator.calculate(dataframe)

        self.assertEqual(
            profile["cardinality_summary"],
            {
                "high_cardinality_columns": ["identifier"],
                "low_cardinality_columns": ["constant"],
            },
        )

    def test_calculate_handles_empty_dataframe(self):
        dataframe = pd.DataFrame({"amount": pd.Series([], dtype="float")})

        profile = self.calculator.calculate(dataframe)

        self.assertEqual(profile["rows_count"], 0)
        self.assertEqual(profile["columns_count"], 1)
        self.assertEqual(
            profile["columns"][0],
            {
                "name": "amount",
                "type": "numeric",
                "nullable": False,
                "null_count": 0,
                "null_percentage": 0.0,
                "cardinality": 0,
                "statistics": {"min": 10.0},
            },
        )
        self.assertEqual(
            profile["cardinality_summary"],
            {
                "high_cardinality_columns": [],
                "low_cardinality_columns": ["amount"],
            },
        )

    def test_calculate_percentage_returns_zero_when_total_is_zero(self):
        percentage = self.calculator._calculate_percentage(5, 0)

        self.assertEqual(percentage, 0.0)


if __name__ == "__main__":
    unittest.main()
