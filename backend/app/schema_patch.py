from __future__ import annotations

from sqlalchemy import text

from .database import engine


BASE_INFO_COLUMNS = {
    "city_population_10k": "FLOAT",
    "population_5km_10k": "FLOAT",
    "population_3km_10k": "FLOAT",
    "city_circle_level": "TEXT",
    "competition_market_level": "TEXT",
    "housing_price_5km": "FLOAT",
    "disposable_income_10k": "FLOAT",
    "regional_function_level": "TEXT",
    "commercial_planning_level": "TEXT",
    "rail_access_level": "TEXT",
    "arterial_access_level": "TEXT",
    "bus_access_level": "TEXT",
    "operation_retrofit_potential_level": "TEXT",
    "asset_rights_complexity_level": "TEXT",
}

SCREENING_RESULT_COLUMNS = {
    "conclusion": "TEXT",
    "risk_note": "TEXT",
    "overall_summary": "TEXT",
    "score_version": "TEXT",
    "data_source_breakdown": "TEXT",
}

CALC_OWNER_COLUMNS = {
    "details_json": "TEXT",
    "params_json": "TEXT",
    "calc_basis": "TEXT",
}

CALC_INTERNAL_COLUMNS = {
    "details_json": "TEXT",
    "params_json": "TEXT",
    "calc_basis": "TEXT",
}

SURVEY_MERCHANT_COLUMNS = {
    "longitude": "FLOAT",
    "latitude": "FLOAT",
    "geocode_status": "TEXT DEFAULT 'pending'",
    "geocode_message": "TEXT",
    "geocoded_at": "TEXT",
    "deleted": "INTEGER NOT NULL DEFAULT 0",
    "deleted_by": "INTEGER",
    "deleted_at": "TEXT",
    "delete_reason": "TEXT",
}

SURVEY_COMPETITOR_COLUMNS = {
    "longitude": "FLOAT",
    "latitude": "FLOAT",
    "geocode_status": "TEXT DEFAULT 'pending'",
    "geocode_message": "TEXT",
    "geocoded_at": "TEXT",
    "deleted": "INTEGER NOT NULL DEFAULT 0",
    "deleted_by": "INTEGER",
    "deleted_at": "TEXT",
    "delete_reason": "TEXT",
}

SURVEY_SUBMISSION_COLUMNS = {
    "deleted": "INTEGER NOT NULL DEFAULT 0",
    "deleted_by": "INTEGER",
    "deleted_at": "TEXT",
    "delete_reason": "TEXT",
}

MARKET_SUBMISSION_COLUMNS = {
    "version": "INTEGER NOT NULL DEFAULT 1",
}


def _existing_columns(conn, table_name: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def _table_exists(conn, table_name: str) -> bool:
    row = conn.execute(
        text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
        ),
        {"table_name": table_name},
    ).fetchone()
    return row is not None


def apply_sqlite_schema_patch() -> None:
    with engine.begin() as conn:
        if conn.dialect.name != "sqlite":
            return

        for table_name, columns in (
            ("project_base_info", BASE_INFO_COLUMNS),
            ("project_screening_result", SCREENING_RESULT_COLUMNS),
            ("calc_asset_owner", CALC_OWNER_COLUMNS),
            ("calc_internal_operation", CALC_INTERNAL_COLUMNS),
            ("survey_submission", SURVEY_SUBMISSION_COLUMNS),
            ("survey_merchant_item", SURVEY_MERCHANT_COLUMNS),
            ("survey_competitor_item", SURVEY_COMPETITOR_COLUMNS),
            ("market_submission", MARKET_SUBMISSION_COLUMNS),
        ):
            if not _table_exists(conn, table_name):
                continue
            existing = _existing_columns(conn, table_name)
            for column_name, column_sql_type in columns.items():
                if column_name in existing:
                    continue
                conn.execute(
                    text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql_type}"
                    )
                )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS project_screening_detail (
                    id TEXT PRIMARY KEY,
                    result_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    indicator_key TEXT NOT NULL,
                    category TEXT NOT NULL,
                    indicator_name TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    mapped_score INTEGER NOT NULL,
                    weight FLOAT NOT NULL,
                    weighted_score FLOAT NOT NULL,
                    note TEXT,
                    source_field TEXT,
                    source_value TEXT,
                    manual_override INTEGER NOT NULL DEFAULT 0
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS survey_submission (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    city TEXT,
                    district TEXT,
                    created_by INTEGER NOT NULL,
                    created_at TEXT,
                    deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_by INTEGER,
                    deleted_at TEXT,
                    delete_reason TEXT
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS survey_merchant_item (
                    id TEXT PRIMARY KEY,
                    submission_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    area_m2 FLOAT NOT NULL,
                    rent_unit_price FLOAT NOT NULL,
                    daily_flow INTEGER NOT NULL,
                    address TEXT NOT NULL,
                    city TEXT NOT NULL,
                    district TEXT NOT NULL,
                    note TEXT,
                    longitude FLOAT,
                    latitude FLOAT,
                    geocode_status TEXT NOT NULL DEFAULT 'pending',
                    geocode_message TEXT,
                    geocoded_at TEXT,
                    created_at TEXT,
                    deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_by INTEGER,
                    deleted_at TEXT,
                    delete_reason TEXT
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS survey_competitor_item (
                    id TEXT PRIMARY KEY,
                    submission_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    scale_m2 FLOAT NOT NULL,
                    avg_rent_unit_price FLOAT NOT NULL,
                    vacancy_rate FLOAT NOT NULL,
                    business_type TEXT NOT NULL,
                    distance_km FLOAT NOT NULL,
                    target_people TEXT NOT NULL,
                    address TEXT NOT NULL,
                    city TEXT NOT NULL,
                    district TEXT NOT NULL,
                    longitude FLOAT,
                    latitude FLOAT,
                    geocode_status TEXT NOT NULL DEFAULT 'pending',
                    geocode_message TEXT,
                    geocoded_at TEXT,
                    created_at TEXT,
                    deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_by INTEGER,
                    deleted_at TEXT,
                    delete_reason TEXT
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS geocode_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_address TEXT UNIQUE,
                    longitude REAL,
                    latitude REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS market_submission (
                    id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL DEFAULT 1,
                    source_mode TEXT NOT NULL,
                    project_id TEXT,
                    city TEXT NOT NULL,
                    district TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at TEXT,
                    deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_by INTEGER,
                    deleted_at TEXT,
                    delete_reason TEXT
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS market_merchant_item (
                    id TEXT PRIMARY KEY,
                    submission_id TEXT NOT NULL,
                    project_id TEXT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    area_m2 FLOAT NOT NULL,
                    rent_unit_price FLOAT NOT NULL,
                    daily_flow INTEGER NOT NULL,
                    address TEXT NOT NULL,
                    city TEXT NOT NULL,
                    district TEXT NOT NULL,
                    note TEXT,
                    longitude FLOAT,
                    latitude FLOAT,
                    geocode_status TEXT NOT NULL DEFAULT 'pending',
                    geocode_message TEXT,
                    geocoded_at TEXT,
                    signature TEXT NOT NULL,
                    created_at TEXT,
                    deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_by INTEGER,
                    deleted_at TEXT,
                    delete_reason TEXT
                )
                """
            )
        )

        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_market_merchant_sig_deleted ON market_merchant_item(signature, deleted)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_market_merchant_active_signature ON market_merchant_item(signature) WHERE deleted = 0"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS market_competitor_item (
                    id TEXT PRIMARY KEY,
                    submission_id TEXT NOT NULL,
                    project_id TEXT,
                    name TEXT NOT NULL,
                    scale_m2 FLOAT NOT NULL,
                    avg_rent_unit_price FLOAT NOT NULL,
                    vacancy_rate FLOAT NOT NULL,
                    business_type TEXT NOT NULL,
                    distance_km FLOAT NOT NULL,
                    target_people TEXT NOT NULL,
                    address TEXT NOT NULL,
                    city TEXT NOT NULL,
                    district TEXT NOT NULL,
                    longitude FLOAT,
                    latitude FLOAT,
                    geocode_status TEXT NOT NULL DEFAULT 'pending',
                    geocode_message TEXT,
                    geocoded_at TEXT,
                    signature TEXT NOT NULL,
                    created_at TEXT,
                    deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_by INTEGER,
                    deleted_at TEXT,
                    delete_reason TEXT
                )
                """
            )
        )

        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_market_competitor_sig_deleted ON market_competitor_item(signature, deleted)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_market_competitor_active_signature ON market_competitor_item(signature) WHERE deleted = 0"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS project_snapshot (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    snapshot_type TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    payload_json TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at TEXT
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_project_snapshot_project_type ON project_snapshot(project_id, snapshot_type, version)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS metric_dictionary (
                    id TEXT PRIMARY KEY,
                    metric_key TEXT NOT NULL UNIQUE,
                    metric_name TEXT NOT NULL,
                    metric_unit TEXT,
                    description TEXT,
                    metric_version TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS intel_source (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL UNIQUE,
                    source_type TEXT NOT NULL,
                    source_url TEXT,
                    is_enabled INTEGER NOT NULL DEFAULT 1,
                    sync_interval_hours INTEGER NOT NULL DEFAULT 6,
                    last_success_at TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS intel_item (
                    id TEXT PRIMARY KEY,
                    item_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    city TEXT,
                    district TEXT,
                    summary TEXT,
                    raw_url TEXT,
                    budget_amount FLOAT,
                    deadline_at TEXT,
                    issuer TEXT,
                    dedupe_key TEXT NOT NULL UNIQUE,
                    payload_json TEXT,
                    matched_rule_count INTEGER NOT NULL DEFAULT 0,
                    follow_up_status TEXT NOT NULL DEFAULT 'none',
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intel_item_type ON intel_item(item_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intel_item_city_district ON intel_item(city, district)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intel_item_published ON intel_item(published_at)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS intel_sync_job (
                    id TEXT PRIMARY KEY,
                    trigger_type TEXT NOT NULL DEFAULT 'manual',
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    status TEXT NOT NULL DEFAULT 'running',
                    window_start TEXT,
                    window_end TEXT,
                    pulled_count INTEGER NOT NULL DEFAULT 0,
                    upserted_count INTEGER NOT NULL DEFAULT 0,
                    deduped_count INTEGER NOT NULL DEFAULT 0,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    created_by INTEGER,
                    source_system TEXT NOT NULL DEFAULT 'bidmonitor',
                    details_json TEXT
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intel_sync_job_started ON intel_sync_job(started_at DESC)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS intel_project_link (
                    id TEXT PRIMARY KEY,
                    intel_item_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    link_type TEXT NOT NULL DEFAULT 'manual',
                    created_by INTEGER NOT NULL,
                    created_at TEXT
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intel_project_link_item ON intel_project_link(intel_item_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intel_project_link_project ON intel_project_link(project_id)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_intel_project_link ON intel_project_link(intel_item_id, project_id)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS intel_watch_rule (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    item_type TEXT NOT NULL DEFAULT 'all',
                    keywords TEXT,
                    city TEXT,
                    district TEXT,
                    budget_min FLOAT,
                    budget_max FLOAT,
                    is_enabled INTEGER NOT NULL DEFAULT 1,
                    created_by INTEGER NOT NULL,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_intel_watch_rule_enabled ON intel_watch_rule(is_enabled)"))

        # Legacy -> market migration (idempotent)
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO market_submission (
                    id, version, source_mode, project_id, city, district, created_by, created_at,
                    deleted, deleted_by, deleted_at, delete_reason
                )
                SELECT
                    id, COALESCE(version, 1), 'project', project_id, COALESCE(city, ''), COALESCE(district, ''), created_by, created_at,
                    COALESCE(deleted, 0), deleted_by, deleted_at, delete_reason
                FROM survey_submission
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO market_merchant_item (
                    id, submission_id, project_id, name, category, area_m2, rent_unit_price, daily_flow,
                    address, city, district, note, longitude, latitude, geocode_status, geocode_message,
                    geocoded_at, signature, created_at, deleted, deleted_by, deleted_at, delete_reason
                )
                SELECT
                    id, submission_id, project_id, name, category, area_m2, rent_unit_price, daily_flow,
                    address, city, district, note, longitude, latitude, geocode_status, geocode_message,
                    geocoded_at,
                    LOWER(TRIM(COALESCE(name, ''))) || '|' || LOWER(TRIM(COALESCE(city, ''))) || '|' || LOWER(TRIM(COALESCE(district, ''))) || '|' || REPLACE(REPLACE(REPLACE(REPLACE(LOWER(TRIM(COALESCE(address, ''))), ' ', ''), '，', ''), ',', ''), '。', ''),
                    created_at, COALESCE(deleted, 0), deleted_by, deleted_at, delete_reason
                FROM survey_merchant_item
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO market_competitor_item (
                    id, submission_id, project_id, name, scale_m2, avg_rent_unit_price, vacancy_rate, business_type,
                    distance_km, target_people, address, city, district, longitude, latitude, geocode_status, geocode_message,
                    geocoded_at, signature, created_at, deleted, deleted_by, deleted_at, delete_reason
                )
                SELECT
                    id, submission_id, project_id, name, scale_m2, avg_rent_unit_price, vacancy_rate, business_type,
                    distance_km, target_people, address, city, district, longitude, latitude, geocode_status, geocode_message,
                    geocoded_at,
                    LOWER(TRIM(COALESCE(name, ''))) || '|' || LOWER(TRIM(COALESCE(city, ''))) || '|' || LOWER(TRIM(COALESCE(district, ''))) || '|' || REPLACE(REPLACE(REPLACE(REPLACE(LOWER(TRIM(COALESCE(address, ''))), ' ', ''), '，', ''), ',', ''), '。', ''),
                    created_at, COALESCE(deleted, 0), deleted_by, deleted_at, delete_reason
                FROM survey_competitor_item
                """
            )
        )
