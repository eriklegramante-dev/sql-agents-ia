from typing import Any

import pandas as pd


class StatisticsCalculator:
    """
    Helper responsible for calculating basic numeric statistics.

    This helper computes descriptive statistical metrics for numeric data.
    It supports calculations for individual dataframe columns as well as
    entire dataframes, returning only meaningful statistics for numeric
    columns while safely ignoring non-numeric or empty data.
    """

    def calculate_for_column(self, series: pd.Series) -> dict[str, Any]:
        """
        Calculate descriptive statistics for a single numeric column.

        The method ignores null values before performing the calculations.
        If the provided series is not numeric or contains no valid values
        after removing nulls, an empty dictionary is returned.

        Args:
            series: Pandas Series representing a dataframe column.

        Returns:
            dict[str, Any]: Dictionary containing the calculated statistics
            for the column, including minimum, maximum, average, and median.
            Returns an empty dictionary when statistics cannot be computed.
        """
        if not pd.api.types.is_numeric_dtype(series):
            return {}

        clean_series = series.dropna()

        if clean_series.empty:
            return {}

        return {
            "min": float(clean_series.min()),
            "max": float(clean_series.max()),
            "average": float(clean_series.mean()),
            "median": float(clean_series.median()),
        }

    def calculate_for_dataframe(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        """
        Calculate descriptive statistics for all numeric columns in a dataframe.

        Only numeric columns are processed. For each eligible column, the
        corresponding statistics are calculated using the column-level
        calculation method.

        Args:
            dataframe: Dataframe containing the data to be analyzed.

        Returns:
            dict[str, Any]: Dictionary mapping each numeric column name to
            its calculated statistical metrics.
        """
        statistics = {}

        numeric_columns = dataframe.select_dtypes(include=["number"])

        for column_name in numeric_columns.columns:
            column_statistics = self.calculate_for_column(
                numeric_columns[column_name]
            )

            if column_statistics:
                statistics[column_name] = column_statistics

        return statistics