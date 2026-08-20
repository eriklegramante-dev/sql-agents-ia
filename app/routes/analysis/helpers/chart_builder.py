from typing import Any, Optional
from app.routes.analysis.dtos.dto import ChartSpec


class ChartSpecBuilder:
    """
    Builder responsible for constructing structured chart specifications.

    Transforms raw analytical query results, axis mappings, and chart
    metadata into a standardized, frontend-friendly ChartSpec structure.
    """

    @staticmethod
    def build(
        chart_type: str,
        title: str,
        x_field: Optional[str],
        y_field: Optional[str],
        rows: list[dict[str, Any]],
    ) -> ChartSpec:
        """
        Builds a structured chart specification instance.

        Combines the resolved chart attributes, selected metric series, and
        raw data rows into a frontend-ready payload.

        Args:
            chart_type:
                Visual representation format (e.g., bar, line, pie, table).
            title:
                Descriptive title for the chart visualization.
            x_field:
                Column name mapped to the horizontal axis or category dimension.
            y_field:
                Column name mapped to the vertical axis or metric dimension.
            rows:
                List of dictionary records returned from analytical execution.

        Returns:
            ChartSpec:
                Structured specification containing chart properties and data points.
        """
        series = [y_field] if y_field else []
        return ChartSpec(
            type=chart_type,
            title=title,
            x_field=x_field,
            y_field=y_field,
            series=series,
            data=rows,
        )