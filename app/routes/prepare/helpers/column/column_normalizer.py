import re

import pandas as pd


class ColumnNormalizer:
    """Normalizes DataFrame column names for prepared datasets.

    Converts names to lowercase snake_case, handles empty or numeric-leading
    names, and disambiguates duplicates while preserving original labels.
    """

    @staticmethod
    def normalize_column_name(name: str) -> str:
        """Normalize one column name to lowercase snake_case.

        Args:
            name (str): Original column name. Non-string values are converted
                with ``str`` before normalization.

        Returns:
            str: Normalized column name. Empty names become ``column`` and
            numeric-leading names receive the ``col_`` prefix.
        """
        normalized = str(name).lower()
        normalized = re.sub(r"[^a-z0-9]", "_", normalized)
        normalized = re.sub(r"_+", "_", normalized)
        normalized = normalized.strip("_")

        if not normalized:
            normalized = "column"

        if normalized[0].isdigit():
            normalized = f"col_{normalized}"

        return normalized

    @staticmethod
    def normalize_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        """Normalize every column name in a DataFrame.

        Args:
            df (pd.DataFrame): DataFrame whose columns should be normalized.

        Returns:
            tuple[pd.DataFrame, list[str]]: Copy of ``df`` with normalized
            column names and the original column labels as strings.
        """
        original_columns = [str(column) for column in df.columns]

        normalized_columns = [
            ColumnNormalizer.normalize_column_name(column)
            for column in original_columns
        ]

        seen: dict[str, int] = {}
        final_columns: list[str] = []

        for column in normalized_columns:
            if column in seen:
                seen[column] += 1
                final_columns.append(f"{column}_{seen[column]}")
            else:
                seen[column] = 0
                final_columns.append(column)

        normalized_df = df.copy()
        normalized_df.columns = final_columns

        return normalized_df, original_columns
