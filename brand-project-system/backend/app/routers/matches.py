"""匹配路由：计算 / 项目推荐品牌 / 品牌推荐项目 / 人工调整。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import matching
from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import Brand, Match, Project
from ..schemas import AdjustIn, ComputeIn, MatchOut
from ..services.classification import build_format_index

router = APIRouter(prefix="/api/v1/matches", tags=["匹配"])


def _to_out(m: Match) -> MatchOut:
    return MatchOut(
        id=m.id, brand_id=m.brand_id, project_id=m.project_id,
        brand_name=m.brand.brand_name if m.brand else None,
        project_name=m.project.project_name if m.project else None,
        dims={
            "format": m.dim_format, "property_condition": m.dim_property_condition,
            "city_region": m.dim_city_region, "positioning_customer": m.dim_positioning_customer,
            "project_type": m.dim_project_type, "business_condition": m.dim_business_condition,
            "expansion_plan": m.dim_expansion_plan, "cooperation_will": m.dim_cooperation_will,
        },
        hard_gate_triggered=m.hard_gate_triggered, hard_gate_reason=m.hard_gate_reason,
        weighted_score=m.weighted_score, data_coverage_rate=m.data_coverage_rate,
        is_formal=m.is_formal, match_grade=m.match_grade,
        satisfied=(m.satisfied_conditions or "").split(";") if m.satisfied_conditions else [],
        unsatisfied=(m.unsatisfied_conditions or "").split(";") if m.unsatisfied_conditions else [],
        pending=(m.pending_conditions or "").split(";") if m.pending_conditions else [],
        manual_adjust=m.manual_adjust, final_score=m.final_score,
        priority=m.priority, rule_version=m.rule_version,
    )


def _persist(db: Session, brand: Brand, project: Project,
             cat_index: dict[str, str] | None = None) -> Match:
    r = matching.compute(brand, project, cat_index)
    final = (r.weighted_score or 0.0)
    m = (db.query(Match).filter(Match.brand_id == brand.id, Match.project_id == project.id,
                                Match.rule_version == r.rule_version).first())
    if not m:
        m = Match(brand_id=brand.id, project_id=project.id, rule_version=r.rule_version)
        db.add(m)
    d = r.dims
    m.dim_format = d["format"]; m.dim_property_condition = d["property_condition"]
    m.dim_city_region = d["city_region"]; m.dim_positioning_customer = d["positioning_customer"]
    m.dim_project_type = d["project_type"]; m.dim_business_condition = d["business_condition"]
    m.dim_expansion_plan = d["expansion_plan"]; m.dim_cooperation_will = d["cooperation_will"]
    m.hard_gate_triggered = r.hard_gate_triggered; m.hard_gate_reason = r.hard_gate_reason
    m.weighted_score = r.weighted_score; m.data_coverage_rate = r.data_coverage_rate
    m.is_formal = r.is_formal; m.match_grade = r.match_grade
    m.satisfied_conditions = ";".join(r.satisfied)
    m.unsatisfied_conditions = ";".join(r.unsatisfied)
    m.pending_conditions = ";".join(r.pending)
    m.manual_adjust = m.manual_adjust or 0.0
    m.final_score = round(final + (m.manual_adjust or 0.0), 2)
    m.priority = matching._grade_of(m.final_score) if not r.hard_gate_triggered else "暂不匹配"
    m.match_code = m.match_code or f"M-{brand.id:04d}-{project.id:04d}"
    return m


@router.post("/compute", response_model=MatchOut)
def compute(body: ComputeIn, db: Session = Depends(get_db),
            _=Depends(require_perm("match:write"))):
    brand = db.get(Brand, body.brand_id, options=[joinedload(Brand.expansion)])
    project = db.get(Project, body.project_id, options=[joinedload(Project.location)])
    if not brand or not project:
        raise HTTPException(404, "品牌或项目不存在")
    m = _persist(db, brand, project, build_format_index(db))
    db.commit(); db.refresh(m)
    return _to_out(m)


@router.post("/{match_id}/adjust", response_model=MatchOut)
def adjust(match_id: int, body: AdjustIn, db: Session = Depends(get_db),
           _=Depends(require_perm("match:write"))):
    m = db.get(Match, match_id)
    if not m:
        raise HTTPException(404, "匹配不存在")
    if abs(body.manual_adjust) > matching.ADJUST_CAP:
        raise HTTPException(400, f"人工调整幅度不得超过 ±{matching.ADJUST_CAP} 分")
    if not body.reason.strip():
        raise HTTPException(400, "人工调整必须填写原因")
    base = (m.weighted_score or 0.0)
    m.manual_adjust = body.manual_adjust
    m.adjust_reason = body.reason
    m.final_score = round(base + body.manual_adjust, 2)
    m.priority = matching._grade_of(m.final_score) if not m.hard_gate_triggered else "暂不匹配"
    db.commit(); db.refresh(m)
    return _to_out(m)


def _result_to_out(brand: Brand, project: Project, r: matching.MatchResult) -> MatchOut:
    final = 0.0 if r.hard_gate_triggered else round(r.weighted_score or 0.0, 2)
    return MatchOut(
        id=None, brand_id=brand.id, project_id=project.id,
        brand_name=brand.brand_name, project_name=project.project_name, dims=r.dims,
        hard_gate_triggered=r.hard_gate_triggered, hard_gate_reason=r.hard_gate_reason,
        weighted_score=r.weighted_score, data_coverage_rate=r.data_coverage_rate,
        is_formal=r.is_formal, match_grade=r.match_grade, satisfied=r.satisfied,
        unsatisfied=r.unsatisfied, pending=r.pending, manual_adjust=0, final_score=final,
        priority=r.match_grade, rule_version=r.rule_version)


@router.get("/by-project/{project_id}", response_model=list[MatchOut])
def recommended_brands(project_id: int, db: Session = Depends(get_db),
                       _=Depends(get_current_user)):
    """项目推荐品牌：对全部品牌实时计算并按分排序。**只读不落库**（落库走 POST /compute）。"""
    project = db.get(Project, project_id, options=[joinedload(Project.location)])
    if not project:
        raise HTTPException(404, "项目不存在")
    brands = db.query(Brand).options(joinedload(Brand.expansion)).filter(
        Brand.is_deleted.is_(False)).all()
    cat_index = build_format_index(db)
    outs = [_result_to_out(b, project, matching.compute(b, project, cat_index)) for b in brands]
    outs.sort(key=lambda m: (m.final_score if m.final_score is not None else -1), reverse=True)
    return outs
