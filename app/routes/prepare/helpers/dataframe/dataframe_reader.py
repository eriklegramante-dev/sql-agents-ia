from io import BytesIO

import pandas as pd


class DataFrameReader:
    """Loads uploaded tabular bytes into a pandas DataFrame.

    Chooses the parser from the object key extension and currently supports CSV
    and XLSX inputs.
    """

    @staticmethod
    def read_file(file_data: bytes, object_key: str) -> pd.DataFrame:
        """Parse tabular bytes according to the object key extension.

        Args:
            file_data (bytes): Raw file content read from storage.
            object_key (str): Storage object key or filename used to detect the
                file extension.

        Returns:
            pd.DataFrame: Parsed tabular data.

        Raises:
            ValueError: If ``object_key`` does not end with ``.csv`` or
                ``.xlsx``.
        """
        object_key_lower = object_key.lower()

        if object_key_lower.endswith(".csv"):
            return pd.read_csv(BytesIO(file_data))

        if object_key_lower.endswith(".xlsx"):
            return pd.read_excel(BytesIO(file_data))

        raise ValueError("Unsupported file format. Only CSV and XLSX are supported.")
