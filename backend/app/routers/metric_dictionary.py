from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import MetricDictionary

router = APIRouter(prefix="/api/metric-dictionary", tags=["metric-dictionary"])

DEFAULT_METRICS = [
    ("city_population_10k", "城市人口", "万人", "筛选模型人口基线"),
    ("population_5km_10k", "项目周边5km人口", "万人", "主力客群半径支撑"),
    ("population_3km_10k", "项目周边3km人口", "万人", "近场消费支撑"),
    ("rent_unit_price", "租金单价", "元/㎡/月", "商家调研租金口径"),
    ("vacancy_rate", "空置率", "%", "竞品经营健康度"),
    ("daily_flow", "日均客流", "人", "商家经营规模"),
]


@router.get("")
def list_metric_dictionary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    _ = user
    now = datetime.utcnow().isoformat(timespec="seconds")
    for key, name, unit, desc in DEFAULT_METRICS:
        exists = db.query(MetricDictionary).filter(MetricDictionary.metric_key == key).first()
        if exists:
            continue
        db.add(
            MetricDictionary(
                id=f"metric-{key}",
                metric_key=key,
                metric_name=name,
                metric_unit=unit,
                description=desc,
                metric_version="v1",
                enabled=1,
                created_at=now,
                updated_at=now,
            )
        )
    db.commit()
    rows = db.query(MetricDictionary).order_by(MetricDictionary.metric_key.asc()).all()
    return [
        {
            "id": row.id,
            "metric_key": row.metric_key,
            "metric_name": row.metric_name,
            "metric_unit": row.metric_unit,
            "description": row.description,
            "metric_version": row.metric_version,
            "enabled": bool(row.enabled),
            "updated_at": row.updated_at,
        }
        for row in rows
    ]
