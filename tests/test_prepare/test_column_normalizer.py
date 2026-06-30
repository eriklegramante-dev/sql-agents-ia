import unittest

import pandas as pd

from app.routes.prepare.helpers.column.column_normalizer import ColumnNormalizer


class ColumnNormalizerTest(unittest.TestCase):
    def test_normalizes_invalid_duplicate_and_numeric_column_names(self):
        df = pd.DataFrame(
            {
                " Total R$ ": [10],
                "Total R$": [20],
                "2026 score": [30],
                "!!!": [40],
            }
        )

        normalized_df, original_columns = ColumnNormalizer.normalize_columns(df)

        self.assertEqual(
            normalized_df.columns.tolist(),
            ["total_r", "total_r_1", "col_2026_score", "column"],
        )
        self.assertEqual(
            original_columns,
            [" Total R$ ", "Total R$", "2026 score", "!!!"],
        )
        self.assertEqual(df.columns.tolist()[0], " Total R$ ")


if __name__ == "__main__":
    unittest.main()
