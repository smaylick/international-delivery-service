from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# id‑ы оставляем без изменений
revision: str = "d062d62f3b6b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "package_types",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
    )
    op.create_index("ix_package_types_id", "package_types", ["id"])

    op.create_table(
        "packages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("session", sa.String(32), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("weight", sa.Float, nullable=False),
        sa.Column("content_cost_usd", sa.Float, nullable=False),
        sa.Column("delivery_cost_rub", sa.Float),
        sa.Column(
            "type_id", sa.Integer, sa.ForeignKey("package_types.id"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_index("ix_packages_session", table_name="packages")
    op.drop_index("ix_packages_id", table_name="packages")
    op.drop_table("packages")

    op.drop_index("ix_package_types_id", table_name="package_types")
    op.drop_table("package_types")
