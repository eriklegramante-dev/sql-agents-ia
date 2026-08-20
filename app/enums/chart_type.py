from enum import Enum


class ChartType(str, Enum):
    """
    Supported chart visualization types for dataset analysis.

    Defines the safe and supported set of visual representations that can
    be generated from analytical query results.

    Attributes:
        BAR:
            Standard vertical or horizontal bar chart representation.
        LINE:
            Time-series or continuous trend line chart representation.
        PIE:
            Proportional distribution or share representation.
        TABLE:
            Tabular structured representation of analytical records.
    """

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"