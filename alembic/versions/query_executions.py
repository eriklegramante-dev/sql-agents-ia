"""Record successful analytical query executions."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "query_executions"
down_revision = "dataset_owner_integer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create execution history with a positive owner constraint and owner index.

    Dataset identifiers are stored without a foreign key. History is not
    coupled to dataset deletion by this migration.
    """
    op.create_table(
        "query_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("user_id > 0", name="ck_query_executions_user_id"),
    )
    op.create_index(
        "ix_query_executions_user_id",
        "query_executions",
        ["user_id"],
    )


def downgrade() -> None:
    """Drop execution history and its user index, discarding stored records.
    """
    op.drop_index(
        "ix_query_executions_user_id",
        table_name="query_executions",
    )
    op.drop_table("query_executions")