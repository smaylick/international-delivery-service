"""insert initial package types

Revision ID: e01417f4d47d
Revises: d062d62f3b6b
Create Date: 2025-05-07 17:25:43.223267

"""

from typing import Sequence, Union
from alembic import op


revision: str = "e01417f4d47d"
down_revision: Union[str, None] = "d062d62f3b6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO package_types (name) VALUES 
        ('Одежда'),
        ('Электроника'),
        ('Разное');
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM package_types WHERE name IN ('Одежда', 'Электроника', 'Разное');
        """
    )
