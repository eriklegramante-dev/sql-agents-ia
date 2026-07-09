import pandas as pd


class ColumnClassifier:
    """
    Helper responsible for classifying dataframe columns.

    This helper determines the logical data type of a dataframe column based on
    its pandas dtype. The inferred type is used by the profiling module to
    generate consistent metadata and provide a simplified representation of the
    dataset schema for downstream consumers.
    """

    def classify(self, series: pd.Series) -> str:
        """
        Classify a dataframe column into a logical data type.

        The method inspects the pandas dtype of the provided series and maps it
        to one of the supported logical types used by the profiling workflow.

        Supported classifications include:
        - numeric
        - boolean
        - datetime
        - text
        - unknown

        Args:
            series: Pandas Series representing a dataframe column.

        Returns:
            str: Logical type inferred for the provided column.
        """
        if pd.api.types.is_bool_dtype(series):
            return "boolean"

        if pd.api.types.is_numeric_dtype(series):
            return "numeric"

        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"

        if isinstance(series.dtype, pd.CategoricalDtype):
            return "unknown"

        if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            return "text"

        return "unknown"
