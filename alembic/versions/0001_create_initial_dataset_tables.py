"""create initial dataset tables

Revision ID: 0001
Revises:
Create Date: 2026-07-21

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    dataset_status_enum = postgresql.ENUM(
        "UPLOADING",
        "COMPLETED",
        "PREPARING",
        "PREPARED",
        "PROFILING",
        "PROFILED",
        "FAILED",
        "DELETED",
        name="dataset_status",
    )

    op.create_table(
        "datasets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "filename",
            sa.String(length=255),
            nullable=True,
        ),        
        sa.Column(
            "status",
            dataset_status_enum,
            nullable=False,
            server_default="UPLOADING",
        ),
        sa.Column(
            "raw_object_key",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "prepared_object_key",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "file_type",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "content_type",
            sa.String(length=100),
            nullable=True,
        ),        
        sa.Column(
            "file_size_bytes",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "current_upload_job_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "rows_count",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "columns_count",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    op.create_table(
        "dataset_schemas",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "columns",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "dataset_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "profile",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("dataset_profiles")
    op.drop_table("dataset_schemas")
    op.drop_table("datasets")

    dataset_status_enum = postgresql.ENUM(
        name="dataset_status"
    )

    dataset_status_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )