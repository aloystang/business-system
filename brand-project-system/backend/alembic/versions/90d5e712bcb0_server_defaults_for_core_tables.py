"""server defaults for core tables

给核心表的时间戳/布尔/枚举 NOT NULL 列补 server_default，使裸 SQL 插入也稳
（应用经 ORM 写入本就有 Python 默认值）。批量模式，SQLite/Postgres 通吃。

Revision ID: 90d5e712bcb0
Revises: 25161e872752
Create Date: 2026-09-05
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "90d5e712bcb0"
down_revision: Union[str, None] = "25161e872752"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NOW = sa.text("CURRENT_TIMESTAMP")
_F, _T = sa.false(), sa.true()

# (表, 列, 类型, server_default)
_DEFAULTS = [
    ("users", "is_active", sa.Boolean(), _T),
    ("users", "created_at", sa.DateTime(), _NOW),
    ("users", "updated_at", sa.DateTime(), _NOW),
    ("brands", "is_deleted", sa.Boolean(), _F),
    ("brands", "created_at", sa.DateTime(), _NOW),
    ("projects", "is_sensitive", sa.Boolean(), _F),
    ("projects", "is_deleted", sa.Boolean(), _F),
    ("projects", "created_at", sa.DateTime(), _NOW),
    ("project_locations", "coordinate_system", sa.String(16), sa.text("'GCJ-02'")),
    ("project_locations", "geocoding_status", sa.String(32), sa.text("'待定位'")),
    ("project_locations", "manually_adjusted", sa.Boolean(), _F),
    ("brand_project_matches", "hard_gate_triggered", sa.Boolean(), _F),
    ("brand_project_matches", "is_formal", sa.Boolean(), _T),
    ("brand_project_matches", "manual_adjust", sa.Float(), sa.text("0")),
    ("brand_project_matches", "rule_version", sa.String(32), sa.text("'v1.0'")),
    ("brand_project_matches", "created_at", sa.DateTime(), _NOW),
]


def _apply(server_default_getter) -> None:
    # 按表分组，逐表 batch，避免 SQLite 多次重建
    by_table: dict[str, list] = {}
    for table, col, coltype, default in _DEFAULTS:
        by_table.setdefault(table, []).append((col, coltype, default))
    for table, cols in by_table.items():
        with op.batch_alter_table(table) as b:
            for col, coltype, default in cols:
                b.alter_column(col, existing_type=coltype,
                               server_default=server_default_getter(default))


def upgrade() -> None:
    _apply(lambda d: d)


def downgrade() -> None:
    _apply(lambda d: None)
