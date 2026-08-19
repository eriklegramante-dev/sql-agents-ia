from dataclasses import dataclass
from typing import List


@dataclass
class ChartPlan:
    sql: str
    chart_type: str
    x_field: str
    y_field: str
    title: str


class ChartPlannerTool:
    """Helper de planejamento simples para o POC."""

    def plan_chart(self, question: str, table_name: str, schema_columns: List[str]) -> ChartPlan:
        q_lower = question.lower()
        x_col = schema_columns[0] if schema_columns else "id"
        y_col = schema_columns[1] if len(schema_columns) > 1 else schema_columns[0]

        if "line" in q_lower or "over time" in q_lower:
            chart_type = "line"
        elif "pie" in q_lower or "share" in q_lower:
            chart_type = "pie"
        else:
            chart_type = "bar"

        sql = f"SELECT {x_col}, COUNT({y_col}) AS total FROM {table_name} GROUP BY {x_col} ORDER BY total DESC"

        return ChartPlan(
            sql=sql,
            chart_type=chart_type,
            x_field=x_col,
            y_field="total",
            title=f"Chart for: {question}",
        )