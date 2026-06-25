from io import BytesIO

import pandas as pd


class ParquetWriter:
    """Serializes prepared DataFrames to Parquet bytes.

    Produces the binary payload written to prepared storage by the workflow.
    """

    @staticmethod
    def dataframe_to_parquet_bytes(df: pd.DataFrame) -> bytes:
        """Serialize a DataFrame to an in-memory Parquet payload.

        Args:
            df (pd.DataFrame): Prepared DataFrame to serialize.

        Returns:
            bytes: Parquet file bytes generated with the ``pyarrow`` engine.
        """
        buffer = BytesIO()
        df.to_parquet(buffer, index=False, engine="pyarrow")
        return buffer.getvalue()
