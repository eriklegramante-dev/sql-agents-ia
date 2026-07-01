import unittest

import pandas as pd

from app.routes.prepare.helpers.schema.schema_inferer import SchemaInferer


class SchemaInfererTest(unittest.TestCase):
    def test_process_dataframe_infers_types_converts_values_and_reports_warnings(self):
        df = pd.DataFrame(
            {
                "Amount": [
                    "10",
                    "20",
                    "30",
                    "40",
                    "50",
                    "60",
                    "70",
                    "80",
                    "90",
                    "oops",
                ],
                "Paid": [
                    "yes",
                    "no",
                    None,
                    "true",
                    "false",
                    "yes",
                    "no",
                    "true",
                    "false",
                    "yes",
                ],
                "Created At": [
                    "2026-06-01",
                    "2026-06-02",
                    None,
                    "2026-06-03",
                    "2026-06-04",
                    "2026-06-05",
                    "2026-06-06",
                    "2026-06-07",
                    "2026-06-08",
                    "2026-06-09",
                ],
                " Notes ": [" ok ", "", None, "done", "x", "y", "z", "a", "b", "c"],
            }
        )

        processed_df, schema, rows_count, columns_count = SchemaInferer.process_dataframe(
            df
        )

        self.assertEqual(rows_count, 10)
        self.assertEqual(columns_count, 4)
        self.assertEqual(
            processed_df.columns.tolist(),
            ["amount", "paid", "created_at", "notes"],
        )

        schema_by_name = {column.name: column for column in schema}
        self.assertEqual(schema_by_name["amount"].data_type, "numeric")
        self.assertEqual(
            schema_by_name["amount"].warnings,
            ["1 value(s) could not be converted to numeric"],
        )
        self.assertTrue(pd.isna(processed_df.loc[9, "amount"]))

        self.assertEqual(schema_by_name["paid"].data_type, "boolean")
        self.assertEqual(processed_df["paid"].tolist()[:2], [True, False])

        self.assertEqual(schema_by_name["created_at"].data_type, "datetime")
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(processed_df["created_at"]))

        self.assertEqual(schema_by_name["notes"].data_type, "string")
        self.assertEqual(processed_df.loc[0, "notes"], "ok")
        self.assertTrue(pd.isna(processed_df.loc[1, "notes"]))

    def test_process_dataframe_infers_empty_series_as_nullable_string(self):
        df = pd.DataFrame({"Empty": [None, None, None]})

        processed_df, schema, rows_count, columns_count = SchemaInferer.process_dataframe(
            df
        )

        self.assertEqual(rows_count, 3)
        self.assertEqual(columns_count, 1)
        self.assertEqual(processed_df.columns.tolist(), ["empty"])
        self.assertEqual(schema[0].data_type, "string")
        self.assertTrue(schema[0].nullable)
        self.assertEqual(schema[0].sample_values, [])

    def test_process_dataframe_reports_datetime_conversion_warning(self):
        df = pd.DataFrame(
            {
                "Created At": [
                    "2026-06-01",
                    "2026-06-02",
                    "2026-06-03",
                    "2026-06-04",
                    "2026-06-05",
                    "2026-06-06",
                    "2026-06-07",
                    "2026-06-08",
                    "2026-06-09",
                    "not-a-date",
                ]
            }
        )

        processed_df, schema, _, _ = SchemaInferer.process_dataframe(df)

        self.assertEqual(schema[0].data_type, "datetime")
        self.assertEqual(
            schema[0].warnings,
            ["1 value(s) could not be converted to datetime"],
        )
        self.assertTrue(pd.isna(processed_df.loc[9, "created_at"]))

    def test_safe_convert_values_reports_boolean_conversion_warning(self):
        series = pd.Series(["yes", "no", "maybe", None])

        converted, warnings = SchemaInferer.safe_convert_values(series, "boolean")

        self.assertEqual(converted.tolist()[:2], [True, False])
        self.assertTrue(pd.isna(converted.iloc[2]))
        self.assertTrue(pd.isna(converted.iloc[3]))
        self.assertEqual(
            warnings,
            ["1 value(s) could not be converted to boolean"],
        )


if __name__ == "__main__":
    unittest.main()
