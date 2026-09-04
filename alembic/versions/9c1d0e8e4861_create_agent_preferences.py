"""create agent_preferences

Revision ID: 9c1d0e8e4861
Revises: 0001
Create Date: 2026-09-04 09:29:08.716089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c1d0e8e4861'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS agent_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            api_key VARCHAR(255),
            persona VARCHAR(100) DEFAULT 'executive',
            model VARCHAR(50) DEFAULT 'gpt-5',
            temperature NUMERIC(3, 2) DEFAULT 0.50,
            response_styles JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_agent_preferences_user_id ON agent_preferences(user_id);")


def downgrade():
    op.execute("DROP INDEX IF NOT EXISTS idx_agent_preferences_user_id;")
    op.execute("DROP TABLE IF NOT EXISTS agent_preferences;")