from typing import Any, Dict, List, Optional
from app.routes.analysis.dtos.dto import ChartSpec


class ChartSpecBuilder:
    @staticmethod
    def build(
        chart_type: str,
        title: str,
        x_field: Optional[str],
        y_field: Optional[str],
        rows: List[Dict[str, Any]],
    ) -> ChartSpec:
        series = [y_field] if y_field else []
        return ChartSpec(
            type=chart_type,
            title=title,
            x_field=x_field,
            y_field=y_field,
            series=series,
            data=rows,
        )