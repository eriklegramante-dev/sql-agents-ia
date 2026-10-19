"""Align dataset ownership with backend integer user IDs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "dataset_owner_integer"
down_revision = "9c1d0e8e4861"
branch_labels = None
depends_on = None


def _require_empty_owners() -> None:
    """Lock datasets and reject conversion when any owner is assigned.

    Raises:
        sqlalchemy.exc.DBAPIError: If PostgreSQL finds a non-null owner or
            cannot acquire the table lock or execute the guard.

    No UUID-to-integer identity mapping is performed here.
    """
    op.execute("LOCK TABLE datasets IN ACCESS EXCLUSIVE MODE")

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM datasets WHERE user_id IS NOT NULL
            ) THEN
                RAISE EXCEPTION
                    'Dataset owner conversion requires an explicit mapping: '
                    'non-null user_id values exist.';
            END IF;
        END
        $$;
    """)


def upgrade() -> None:
    """Convert nullable UUID owners to integers and add the owner index.

    Requires all existing owners to be null. Assigned legacy owners need
    an explicit migration plan; this revision provides no identity mapping.
    Unassigned datasets remain unassigned.
    """
    _require_empty_owners()

    op.alter_column(
        "datasets",
        "user_id",
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="NULL::integer",
    )

    op.create_index(
        "ix_datasets_user_id",
        "datasets",
        ["user_id"],
    )


def downgrade() -> None:
    """Restore nullable UUID owners only when no integer owner is assigned.

    The same guard used by upgrade rejects rollback after owned datasets
    have been created; no automatic reverse identity mapping is provided.
    """
    _require_empty_owners()

    op.drop_index("ix_datasets_user_id", table_name="datasets")

    op.alter_column(
        "datasets",
        "user_id",
        existing_type=sa.Integer(),
        type_=postgresql.UUID(as_uuid=True),
        existing_nullable=True,
        postgresql_using="NULL::uuid",
    )
