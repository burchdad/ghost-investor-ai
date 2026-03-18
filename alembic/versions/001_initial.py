"""Initial schema migration."""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    # Run: alembic upgrade head
    pass


def downgrade() -> None:
    """Drop initial tables."""
    pass
