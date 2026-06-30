from io import BytesIO
import unittest

import pandas as pd

from app.routes.prepare.helpers.dataframe.dataframe_reader import DataFrameReader
from app.routes.prepare.helpers.parquet.parquet_writer import ParquetWriter


class DataFrameReaderAndParquetWriterTest(unittest.TestCase):
    def test_reads_csv_and_rejects_unsupported_formats(self):
        csv_data = b"name,age\nAna,30\n"

        df = DataFrameReader.read_file(csv_data, "people.CSV")

        self.assertEqual(df.to_dict("records"), [{"name": "Ana", "age": 30}])
        with self.assertRaisesRegex(ValueError, "Unsupported file format"):
            DataFrameReader.read_file(b"{}", "people.json")

    def test_reads_xlsx(self):
        source_df = pd.DataFrame({"name": ["Ana", "Bia"], "age": [30, 25]})
        buffer = BytesIO()
        source_df.to_excel(buffer, index=False)

        df = DataFrameReader.read_file(buffer.getvalue(), "people.XLSX")

        pd.testing.assert_frame_equal(df, source_df)

    def test_writes_parquet_bytes_readable_by_pandas(self):
        df = pd.DataFrame({"id": [1, 2], "name": ["Ana", "Bia"]})

        parquet_data = ParquetWriter.dataframe_to_parquet_bytes(df)
        restored_df = pd.read_parquet(BytesIO(parquet_data), engine="pyarrow")

        pd.testing.assert_frame_equal(restored_df, df)


if __name__ == "__main__":
    unittest.main()
