"""brand expansion: property_preference + opening_plan

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-09-27 09:00:00.000000

补品牌拓展要求的"物业偏好"与"开店计划"，此前前端一直显示演示假数据，
本次接入真实台账，需要落库承载。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("brand_expansion_requirements") as batch:
        batch.add_column(sa.Column("property_preference", sa.String(length=200), nullable=True))
        batch.add_column(sa.Column("opening_plan", sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("brand_expansion_requirements") as batch:
        batch.drop_column("opening_plan")
        batch.drop_column("property_preference")
