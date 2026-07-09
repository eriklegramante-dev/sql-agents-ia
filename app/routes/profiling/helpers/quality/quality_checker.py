import pandas as pd


class QualityChecker:
    """
    Helper responsible for generating basic data quality warnings.

    This helper evaluates a dataframe against a set of predefined quality
    rules and identifies common issues that may affect downstream processing
    or analytical results. The generated warnings provide a concise overview
    of potential data quality problems, such as excessive missing values,
    empty columns, high-cardinality identifiers, and columns containing only
    a single distinct value.

    The quality assessment is intentionally lightweight and is designed to
    complement the profiling metadata generated during the dataset profiling
    workflow without modifying the original dataset.
    """

    def check(self, dataframe: pd.DataFrame) -> list[str]:
        """
        Analyze a dataframe and generate quality warnings.

        Each column is evaluated independently to identify common quality
        issues. When a rule is violated, a descriptive warning message is
        added to the resulting list.

        Current validation rules include:
        - Columns with at least 80% null values.
        - Completely empty columns.
        - Columns whose cardinality matches the total number of rows.
        - Columns containing only one distinct value.

        Args:
            dataframe: Dataframe to be analyzed.

        Returns:
            list[str]: Collection of quality warning messages generated from
            the dataframe analysis.
        """
        warnings = []
        rows_count = len(dataframe)

        for column_name in dataframe.columns:
            series = dataframe[column_name]
            null_count = int(series.isna().sum())
            cardinality = int(series.nunique(dropna=True))
            null_percentage = self._calculate_percentage(null_count, rows_count)

            if rows_count > 0 and null_percentage >= 80:
                warnings.append(
                    f"Column '{column_name}' has a high null percentage."
                )

            if cardinality == 0:
                warnings.append(f"Column '{column_name}' is empty.")

            if rows_count > 0 and cardinality == rows_count:
                warnings.append(
                    f"Column '{column_name}' has suspiciously high cardinality."
                )

            if cardinality == 1:
                warnings.append(
                    f"Column '{column_name}' contains only one distinct value."
                )

        return warnings

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