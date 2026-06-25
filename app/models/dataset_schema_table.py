from typing import Any

from pydantic import BaseModel


class ColumnSchema(BaseModel):
    """Describes one column inferred from a prepared dataset.

    Stores the normalized and original names, inferred data type, nullability,
    sample values, and non-fatal conversion warnings.
    """

    name: str
    original_name: str
    data_type: str
    nullable: bool
    sample_values: list[Any]
    warnings: list[str] = []
