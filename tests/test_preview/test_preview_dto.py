import unittest

from pydantic import ValidationError

from app.routes.preview.dtos.dto import DatasetPreviewRequestDTO
from tests.helpers import DATASET_ID


class DatasetPreviewRequestDTOTest(unittest.TestCase):
    def test_normalizes_missing_limit_to_default(self):
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit=None,
        )

        self.assertEqual(request.limit, 20)

    def test_normalizes_empty_limit_to_default(self):
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit="",
        )

        self.assertEqual(request.limit, 20)

    def test_converts_string_limit_to_int(self):
        request = DatasetPreviewRequestDTO(
            dataset_id=DATASET_ID,
            limit="10",
        )

        self.assertEqual(request.limit, 10)

    def test_rejects_limit_lower_than_one(self):
        with self.assertRaises(ValidationError):
            DatasetPreviewRequestDTO(
                dataset_id=DATASET_ID,
                limit=0,
            )

    def test_rejects_limit_greater_than_one_hundred(self):
        with self.assertRaises(ValidationError):
            DatasetPreviewRequestDTO(
                dataset_id=DATASET_ID,
                limit=101,
            )


if __name__ == "__main__":
    unittest.main()
