from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from .auth import get_password_hash
from .database import Base, engine, SessionLocal
from .models import ProjectBaseInfo, User, UserRole
from .schema_patch import apply_sqlite_schema_patch


DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",
    "role": UserRole.admin,
}


def ensure_admin(db: Session) -> None:
    existing = db.query(User).filter(User.username == DEFAULT_ADMIN["username"]).first()
    if existing:
        return
    admin = User(
        username=DEFAULT_ADMIN["username"],
        password_hash=get_password_hash(DEFAULT_ADMIN["password"]),
        role=DEFAULT_ADMIN["role"],
        is_active=True,
    )
    db.add(admin)
    db.commit()


def ensure_seed_project(db: Session) -> None:
    existing = db.query(ProjectBaseInfo).filter(ProjectBaseInfo.project_id == "PRJ-0001").first()
    if existing:
        return
    now = datetime.utcnow().isoformat(timespec="seconds")
    seed = ProjectBaseInfo(
        project_id="PRJ-0001",
        project_name="重庆渝中广场",
        city="重庆",
        district="渝中区",
        location_desc="解放碑核心商圈",
        total_area=120000.0,
        rentable_area=80000.0,
        core_area=20000.0,
        asset_distribution="集中",
        ownership_structure="甲方",
        vacancy_rate=12.0,
        rent_min=80.0,
        rent_max=120.0,
        main_business_type="餐饮、零售",
        competitor_list="解放碑广场、时代天街",
        competition_level="强",
        city_population_10k=1200,
        population_5km_10k=58,
        population_3km_10k=36,
        city_circle_level="一线城市核心商圈",
        competition_market_level="3km内无8万㎡以上同业定位商业项目",
        housing_price_5km=22000,
        disposable_income_10k=5.2,
        regional_function_level="城市级大型商务区",
        commercial_planning_level="城市商业区中心核心地点",
        rail_access_level="直接连接轨道交通站点",
        arterial_access_level="有2条城市主干道",
        bus_access_level="5条以上公交站点在项目1公里范围内",
        operation_retrofit_potential_level="低投入可快速提升",
        asset_rights_complexity_level="权属较清晰协同可控",
        remark="种子数据",
        is_confirmed=1,
        created_at=now,
        updated_at=now,
    )
    db.add(seed)
    db.commit()


def main():
    Base.metadata.create_all(bind=engine)
    apply_sqlite_schema_patch()
    db = SessionLocal()
    try:
        ensure_admin(db)
        ensure_seed_project(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
