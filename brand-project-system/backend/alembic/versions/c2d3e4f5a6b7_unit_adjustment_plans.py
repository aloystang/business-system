"""unit adjustment plans (业态调改计划)

Revision ID: c2d3e4f5a6b7
Revises: b1a2c3d4e5f6
Create Date: 2026-09-09 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1a2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "unit_adjustment_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("from_format", sa.String(length=64), nullable=True),
        sa.Column("to_format", sa.String(length=64), nullable=True),
        sa.Column("target_brand_id", sa.Integer(), nullable=True),
        sa.Column("expected_rent", sa.Float(), nullable=True),
        sa.Column("expected_rent_psm", sa.Float(), nullable=True),
        sa.Column("plan_status", sa.String(length=16), server_default="草案", nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"),
                  nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"),
                  nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"]),
        sa.ForeignKeyConstraint(["target_brand_id"], ["brands.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("unit_id", name="uq_adjust_plan_unit"),
    )
    op.create_index("ix_unit_adjustment_plans_project_id", "unit_adjustment_plans",
                    ["project_id"])
    op.create_index("ix_unit_adjustment_plans_unit_id", "unit_adjustment_plans", ["unit_id"])


def downgrade() -> None:
    op.drop_index("ix_unit_adjustment_plans_unit_id", table_name="unit_adjustment_plans")
    op.drop_index("ix_unit_adjustment_plans_project_id", table_name="unit_adjustment_plans")
    op.drop_table("unit_adjustment_plans")
