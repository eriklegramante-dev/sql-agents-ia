import unittest

from pydantic import ValidationError

from app.routes.analysis.dtos.dto import (
    AnalysisQueryRequestDTO,
    AnalysisQueryResponseDTO,
)
from tests.helpers import DATASET_ID


class AnalysisQueryRequestDTOTest(unittest.TestCase):
    def test_normalizes_question_and_sql_values(self):
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            question="  total sales  ",
            sql="  select * from dataset  ",
            limit=5,
        )

        self.assertEqual(request.question, "total sales")
        self.assertEqual(request.sql, "select * from dataset")

    def test_normalizes_empty_question_to_none_when_sql_is_provided(self):
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            question="   ",
            sql="select * from dataset",
        )

        self.assertIsNone(request.question)
        self.assertEqual(request.sql, "select * from dataset")

    def test_normalizes_missing_limit_to_default(self):
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            sql="select * from dataset",
            limit=None,
        )

        self.assertEqual(request.limit, 20)

    def test_normalizes_empty_limit_to_default(self):
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            sql="select * from dataset",
            limit="",
        )

        self.assertEqual(request.limit, 20)

    def test_converts_string_limit_to_int(self):
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            sql="select * from dataset",
            limit="10",
        )

        self.assertEqual(request.limit, 10)

    def test_accepts_question_without_sql(self):
        request = AnalysisQueryRequestDTO(
            dataset_id=DATASET_ID,
            question="What is the total?",
        )

        self.assertEqual(request.question, "What is the total?")
        self.assertIsNone(request.sql)

    def test_rejects_request_without_question_or_sql(self):
        with self.assertRaises(ValidationError):
            AnalysisQueryRequestDTO(
                dataset_id=DATASET_ID,
                question="   ",
                sql=None,
            )

    def test_rejects_non_string_query_value(self):
        with self.assertRaises(ValidationError):
            AnalysisQueryRequestDTO(
                dataset_id=DATASET_ID,
                sql=123,
            )

    def test_rejects_limit_lower_than_one(self):
        with self.assertRaises(ValidationError):
            AnalysisQueryRequestDTO(
                dataset_id=DATASET_ID,
                sql="select * from dataset",
                limit=0,
            )

    def test_rejects_limit_greater_than_one_hundred(self):
        with self.assertRaises(ValidationError):
            AnalysisQueryRequestDTO(
                dataset_id=DATASET_ID,
                sql="select * from dataset",
                limit=101,
            )

    def test_rejects_extra_fields(self):
        with self.assertRaises(ValidationError):
            AnalysisQueryRequestDTO(
                dataset_id=DATASET_ID,
                sql="select * from dataset",
                unexpected=True,
            )


class AnalysisQueryResponseDTOTest(unittest.TestCase):
    def test_builds_response_with_analysis_data(self):
        response = AnalysisQueryResponseDTO(
            success=True,
            message="Analysis query executed successfully.",
            data={
                "dataset_id": DATASET_ID,
                "executed_sql": "select name from dataset",
                "columns": ["name"],
                "rows": [{"name": "Ana"}],
                "rows_count": 1,
                "returned_rows_count": 1,
                "limit": 20,
            },
            errors=None,
        )

        self.assertTrue(response.success)
        self.assertEqual(response.data.dataset_id, DATASET_ID)
        self.assertEqual(response.data.executed_sql, "select name from dataset")
        self.assertEqual(response.data.columns, ["name"])
        self.assertEqual(response.data.rows, [{"name": "Ana"}])
        self.assertEqual(response.data.rows_count, 1)
        self.assertEqual(response.data.returned_rows_count, 1)
        self.assertEqual(response.data.limit, 20)
        self.assertIsNone(response.errors)


if __name__ == "__main__":
    unittest.main()
