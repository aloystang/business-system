"""brand l3_category (三级业态)

Revision ID: b1a2c3d4e5f6
Revises: a572024e4bd4
Create Date: 2026-09-06 11:00:00.000000

给品牌表补第三级业态列，配合 brand_categories 三级业态树落地。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, None] = "a572024e4bd4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("brands") as batch:
        batch.add_column(sa.Column("l3_category", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("brands") as batch:
        batch.drop_column("l3_category")
