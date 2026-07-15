from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "COLOQUE_A_REVISION_GERADA"
down_revision: str | None = "19e972489b5b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        'CREATE EXTENSION IF NOT EXISTS "pgcrypto"'
    )

    op.alter_column(
        "dataset_schemas",
        "id",
        existing_type=sa.UUID(),
        nullable=False,
        server_default=sa.text("gen_random_uuid()"),
    )


def downgrade() -> None:
    op.alter_column(
        "dataset_schemas",
        "id",
        existing_type=sa.UUID(),
        nullable=False,
        server_default=None,
    )