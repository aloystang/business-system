"""postgis enhancements for project_locations

在 Postgres 上为 project_locations 补齐 PostGIS 能力（geom + 触发器 + GiST + CHECK）；
在 SQLite 上为 no-op（本地用 lng/lat）。这样 Alembic 成为单一迁移源，且两库通吃。

Revision ID: 25161e872752
Revises: 58425d0add8b
Create Date: 2026-09-05
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "25161e872752"
down_revision: Union[str, None] = "58425d0add8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SYNC_FN = """
CREATE OR REPLACE FUNCTION sync_project_geom() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.longitude IS NOT NULL AND NEW.latitude IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    ELSE
        NEW.geom = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("ALTER TABLE project_locations ADD COLUMN geom geometry(Point, 4326)")
    op.execute(_SYNC_FN)
    op.execute(
        "CREATE TRIGGER trg_proj_geom BEFORE INSERT OR UPDATE OF longitude, latitude "
        "ON project_locations FOR EACH ROW EXECUTE FUNCTION sync_project_geom()"
    )
    # 回填已有行
    op.execute(
        "UPDATE project_locations "
        "SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) "
        "WHERE longitude IS NOT NULL AND latitude IS NOT NULL"
    )
    op.execute("CREATE INDEX idx_project_geom ON project_locations USING gist (geom)")
    # 定位失败/待定位不得带坐标；成功必须有坐标（与应用层不变量双保险）
    op.execute(
        "ALTER TABLE project_locations ADD CONSTRAINT chk_geocode_coords CHECK ("
        "  (geocoding_status IN ('定位失败','待定位') AND geom IS NULL)"
        "  OR (geocoding_status IN ('自动定位','人工确认','人工修正') AND geom IS NOT NULL))"
    )


def downgrade() -> None:
    if not _is_postgres():
        return
    op.execute("ALTER TABLE project_locations DROP CONSTRAINT IF EXISTS chk_geocode_coords")
    op.execute("DROP INDEX IF EXISTS idx_project_geom")
    op.execute("DROP TRIGGER IF EXISTS trg_proj_geom ON project_locations")
    op.execute("DROP FUNCTION IF EXISTS sync_project_geom()")
    op.execute("ALTER TABLE project_locations DROP COLUMN IF EXISTS geom")
