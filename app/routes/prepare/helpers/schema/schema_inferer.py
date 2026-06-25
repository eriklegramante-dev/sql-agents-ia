from typing import Any

import pandas as pd

from app.models.dataset_schema_table import ColumnSchema
from app.routes.prepare.helpers.column.column_normalizer import ColumnNormalizer


class SchemaInferer:
    """Builds normalized data and schema metadata from a DataFrame.

    Infers numeric, datetime, boolean, or string types, converts values safely,
    and records warnings when conversion drops invalid values.
    """

    @staticmethod
    def infer_column_type(series: pd.Series) -> str:
        """Infer the logical type for one pandas Series.

        Args:
            series (pd.Series): Column values to inspect.

        Returns:
            str: One of ``numeric``, ``datetime``, ``boolean``, or ``string``.
        """
        clean_series = series.dropna()

        if clean_series.empty:
            return "string"

        numeric_series = pd.to_numeric(clean_series, errors="coerce")
        if numeric_series.notna().mean() >= 0.9:
            return "numeric"

        datetime_series = pd.to_datetime(clean_series, errors="coerce")
        if datetime_series.notna().mean() >= 0.9:
            return "datetime"

        lowered_values = set(clean_series.astype(str).str.lower().unique())
        boolean_values = {"true", "false", "1", "0", "yes", "no"}

        if lowered_values and lowered_values.issubset(boolean_values):
            return "boolean"

        return "string"

    @staticmethod
    def safe_convert_values(
        series: pd.Series,
        inferred_type: str,
    ) -> tuple[pd.Series, list[str]]:
        """Convert a Series using a previously inferred logical type.

        Args:
            series (pd.Series): Original column values to convert.
            inferred_type (str): Logical type returned by
                ``infer_column_type``.

        Returns:
            tuple[pd.Series, list[str]]: Converted values and warning messages
            describing values that could not be converted.
        """
        warnings: list[str] = []

        if inferred_type == "numeric":
            converted = pd.to_numeric(series, errors="coerce")
            failed_count = int(converted.isna().sum() - series.isna().sum())

            if failed_count > 0:
                warnings.append(
                    f"{failed_count} value(s) could not be converted to numeric"
                )

            return converted, warnings

        if inferred_type == "datetime":
            converted = pd.to_datetime(series, errors="coerce")
            failed_count = int(converted.isna().sum() - series.isna().sum())

            if failed_count > 0:
                warnings.append(
                    f"{failed_count} value(s) could not be converted to datetime"
                )

            return converted, warnings

        if inferred_type == "boolean":
            boolean_map = {
                "true": True,
                "false": False,
                "1": True,
                "0": False,
                "yes": True,
                "no": False,
            }

            converted = series.apply(
                lambda value: (
                    pd.NA
                    if pd.isna(value)
                    else boolean_map.get(str(value).lower(), pd.NA)
                )
            )

            failed_count = int(converted.isna().sum() - series.isna().sum())

            if failed_count > 0:
                warnings.append(
                    f"{failed_count} value(s) could not be converted to boolean"
                )

            return converted, warnings

        converted = series.astype("string").str.strip()
        converted = converted.replace("", pd.NA)

        return converted, warnings

    @staticmethod
    def process_dataframe(
        df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, list[ColumnSchema], int, int]:
        """Normalize, convert, and describe all columns in a DataFrame.

        Args:
            df (pd.DataFrame): Raw parsed tabular data.

        Returns:
            tuple[pd.DataFrame, list[ColumnSchema], int, int]: Processed
            DataFrame, inferred schema metadata, row count, and column count.
        """
        normalized_df, original_columns = ColumnNormalizer.normalize_columns(df)

        processed_df = normalized_df.copy()
        columns_schema: list[ColumnSchema] = []

        for index, column_name in enumerate(normalized_df.columns):
            series = normalized_df[column_name]
            inferred_type = SchemaInferer.infer_column_type(series)

            converted_series, warnings = SchemaInferer.safe_convert_values(
                series,
                inferred_type,
            )

            processed_df[column_name] = converted_series

            sample_values: list[Any] = (
                converted_series.dropna().head(5).astype(str).tolist()
            )

            columns_schema.append(
                ColumnSchema(
                    name=column_name,
                    original_name=original_columns[index],
                    data_type=inferred_type,
                    nullable=bool(converted_series.isna().any()),
                    sample_values=sample_values,
                    warnings=warnings,
                )
            )

        return processed_df, columns_schema, len(processed_df), len(processed_df.columns)
