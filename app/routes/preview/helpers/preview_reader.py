from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any

import pandas as pd
from pydantic import BaseModel


class PreviewResult(BaseModel):
    """Represents the result generated from reading a dataset preview."""

    columns: list[str]
    rows: list[dict[str, Any]]
    rows_count: int


class PreviewReader:
    """Reads Parquet content and generates a serializable dataset preview."""

    def read(
        self,
        parquet_content: bytes,
        limit: int,
    ) -> PreviewResult:
        dataframe = pd.read_parquet(BytesIO(parquet_content))

        preview_dataframe = dataframe.head(limit).copy()
        preview_dataframe = preview_dataframe.astype(object).where(
            pd.notna(preview_dataframe),
            None,
        )

        rows = [
            {
                column_name: self._serialize_value(value)
                for column_name, value in row.items()
            }
            for row in preview_dataframe.to_dict(orient="records")
        ]

        return PreviewResult(
            columns=[str(column) for column in dataframe.columns],
            rows=rows,
            rows_count=len(dataframe),
        )

    def _serialize_value(self, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        if hasattr(value, "item"):
            return value.item()

        return value