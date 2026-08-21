from typing import Any, Optional

import pandas as pd


from app.routes.profiling.helpers.column.column_classifier import (
    ColumnClassifier,
)
from app.routes.profiling.helpers.quality.quality_checker import (
    QualityChecker,
)
from app.routes.profiling.helpers.statistics.statistics_calculator import (
    StatisticsCalculator,
)


class ProfileCalculator:
    """
    Helper responsible for building dataset profiling metadata.

    This helper centralizes all calculations required to generate a complete
    profile of a prepared dataset. It coordinates column classification,
    statistical analysis, data quality validation, null-value aggregation,
    cardinality analysis, and summary generation.

    The class is intentionally independent from workflow and persistence
    concerns, focusing exclusively on transforming a pandas DataFrame into
    structured profiling metadata that can be persisted and returned by the
    application layers.

    Args:
        column_classifier:
            Helper responsible for identifying the semantic type of each
            dataframe column. When not provided, a default
            ``ColumnClassifier`` instance is created.
        statistics_calculator:
            Helper responsible for computing statistical metrics for columns
            and the entire dataframe. When not provided, a default
            ``StatisticsCalculator`` instance is created.
        quality_checker:
            Helper responsible for validating dataset quality and generating
            warning messages. When not provided, a default
            ``QualityChecker`` instance is created.

    Attributes:
        column_classifier:
            Helper responsible for classifying dataframe columns.
        statistics_calculator:
            Helper responsible for computing descriptive statistics.
        quality_checker:
            Helper responsible for validating data quality and generating
            quality warnings.
    """

    def __init__(
        self,
        column_classifier: Optional[ColumnClassifier] = None,
        statistics_calculator: Optional[StatisticsCalculator] = None,
        quality_checker: Optional[QualityChecker] = None,
    ) -> None:
        self.column_classifier = column_classifier or ColumnClassifier()
        self.statistics_calculator = statistics_calculator or StatisticsCalculator()
        self.quality_checker = quality_checker or QualityChecker()

    def calculate(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        """
        Generate the complete dataset profile.

        The generated profile contains dataset dimensions, column metadata,
        null-value summaries, cardinality information, statistical metrics,
        and quality warnings derived from the provided dataframe.

        Args:
            dataframe: Prepared dataframe that will be analyzed.

        Returns:
            dict[str, Any]: Dictionary containing the complete profiling
            metadata used by the profiling workflow.
        """
        return {
            "rows_count": len(dataframe),
            "columns_count": len(dataframe.columns),
            "columns": self._build_columns_profile(dataframe),
            "nulls_summary": self._build_nulls_summary(dataframe),
            "cardinality_summary": self._build_cardinality_summary(dataframe),
            "basic_statistics": self.statistics_calculator.calculate_for_dataframe(
                dataframe
            ),
            "quality_warnings": self.quality_checker.check(dataframe),
        }

    def _build_columns_profile(self, dataframe: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Build profiling metadata for every dataframe column.

        Each column profile contains information such as inferred data type,
        nullability, null count, null percentage, cardinality, and descriptive
        statistics calculated specifically for that column.

        Args:
            dataframe: Dataframe whose columns will be analyzed.

        Returns:
            list[dict[str, Any]]: List containing profiling metadata for every
            dataframe column.
        """
        columns = []

        for column_name in dataframe.columns:
            series = dataframe[column_name]
            null_count = int(series.isna().sum())
            cardinality = int(series.nunique(dropna=True))

            columns.append(
                {
                    "name": column_name,
                    "type": self.column_classifier.classify(series),
                    "nullable": null_count > 0,
                    "null_count": null_count,
                    "null_percentage": self._calculate_percentage(
                        null_count,
                        len(series),
                    ),
                    "cardinality": cardinality,
                    "statistics": self.statistics_calculator.calculate_for_column(
                        series
                    ),
                }
            )

        return columns

    def _build_nulls_summary(self, dataframe: pd.DataFrame) -> dict[str, int]:
        """
        Generate a summary of null values across the dataframe.

        The summary includes the total number of null values and the number
        of columns that contain at least one missing value.

        Args:
            dataframe: Dataframe to analyze.

        Returns:
            dict[str, int]: Dictionary containing aggregated null-value
            statistics.
        """
        null_counts = dataframe.isna().sum()

        return {
            "total_nulls": int(null_counts.sum()),
            "columns_with_nulls": int((null_counts > 0).sum()),
        }

    def _build_cardinality_summary(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, list[str]]:
        """
        Generate cardinality information for the dataframe.

        Columns are classified according to their number of distinct values,
        identifying columns with very high cardinality and columns containing
        only a single distinct value.

        Args:
            dataframe: Dataframe whose cardinality will be analyzed.

        Returns:
            dict[str, list[str]]: Dictionary containing lists of high- and
            low-cardinality columns.
        """
        rows_count = len(dataframe)
        high_cardinality_columns = []
        low_cardinality_columns = []

        for column_name in dataframe.columns:
            cardinality = int(dataframe[column_name].nunique(dropna=True))

            if rows_count > 0 and cardinality / rows_count >= 0.9:
                high_cardinality_columns.append(column_name)

            if cardinality <= 1:
                low_cardinality_columns.append(column_name)

        return {
            "high_cardinality_columns": high_cardinality_columns,
            "low_cardinality_columns": low_cardinality_columns,
        }

    def _calculate_percentage(self, value: int, total: int) -> float:
        """
        Calculate a percentage while safely handling division by zero.

        Args:
            value: Value that represents the numerator.
            total: Value that represents the denominator.

        Returns:
            float: Percentage rounded to two decimal places. Returns ``0.0``
            when the total is zero.
        """
        if total == 0:
            return 0.0

        return round((value / total) * 100, 2)
