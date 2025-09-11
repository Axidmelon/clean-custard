"""verify_existing_users

Revision ID: adf20122a572
Revises: 20250127_add_agent_id
Create Date: 2025-09-11 06:20:03.365285

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adf20122a572'
down_revision: Union[str, Sequence[str], None] = '20250127_add_agent_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
