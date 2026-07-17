from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
import unittest

import pandas as pd

from app.routes.preview.helpers.preview_reader import PreviewReader


class PreviewReaderTest(unittest.TestCase):
    def make_parquet(self, dataframe: pd.DataFrame) -> bytes:
        buffer = BytesIO()
        dataframe.to_parquet(buffer, index=False)
        return buffer.getvalue()

    def test_reads_limited_rows_and_serializes_values(self):
        dataframe = pd.DataFrame(
            [
                {
                    "id": 1,
                    "name": "Ana",
                    "created_at": datetime(2026, 6, 23, 12, 0, 0),
                    "birthday": date(1990, 1, 2),
                    "score": Decimal("10.5"),
                },
                {
                    "id": 2,
                    "name": None,
                    "created_at": datetime(2026, 6, 24, 12, 0, 0),
                    "birthday": date(1991, 1, 2),
                    "score": Decimal("20.5"),
                },
            ]
        )
        reader = PreviewReader()

        result = reader.read(self.make_parquet(dataframe), limit=1)

        self.assertEqual(
            result.columns,
            ["id", "name", "created_at", "birthday", "score"],
        )
        self.assertEqual(result.rows_count, 2)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0]["id"], 1)
        self.assertEqual(result.rows[0]["created_at"], "2026-06-23T12:00:00")
        self.assertEqual(result.rows[0]["birthday"], "1990-01-02")
        self.assertEqual(result.rows[0]["score"], 10.5)

    def test_converts_missing_values_to_none(self):
        dataframe = pd.DataFrame(
            [
                {"name": "Ana", "age": 30},
                {"name": None, "age": None},
            ]
        )
        reader = PreviewReader()

        result = reader.read(self.make_parquet(dataframe), limit=2)

        self.assertIsNone(result.rows[1]["name"])
        self.assertIsNone(result.rows[1]["age"])


if __name__ == "__main__":
    unittest.main()
