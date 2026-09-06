"""数据导出：品牌/项目列表 + 项目招商报告（Excel / PDF）。"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload

from .. import matching
from ..database import get_db
from ..deps import get_current_user
from ..models import Brand, CandidateList, Project, ProjectScore
from ..services.exporter import build_xlsx
from ..services.pdf_report import build_report_pdf

router = APIRouter(prefix="/api/v1/export", tags=["导出"])
_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_PDF = "application/pdf"


def _download(data: bytes, filename: str, media_type: str) -> Response:
    # 中文文件名走 RFC 5987
    disp = f"attachment; filename*=UTF-8''{quote(filename)}"
    return Response(content=data, media_type=media_type,
                    headers={"Content-Disposition": disp})


def _xlsx_response(data: bytes, filename: str) -> Response:
    return _download(data, filename, _XLSX)


@router.get("/brands.xlsx")
def export_brands(q: str | None = None, l1: str | None = None,
                  db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(Brand).filter(Brand.is_deleted.is_(False))
    if q:
        query = query.filter(Brand.brand_name.like(f"%{q}%"))
    if l1:
        query = query.filter(Brand.l1_category == l1)
    brands = query.order_by(Brand.brand_code).all()
    headers = ["品牌编码", "品牌名称", "一级业态", "标签", "经营状态", "门店数", "总部", "合作意愿", "评分等级"]
    rows = [[b.brand_code, b.brand_name, b.l1_category, b.tags, b.operating_status,
             b.store_count, b.hq_city, b.cooperation_intent, b.grade] for b in brands]
    return _xlsx_response(build_xlsx([("品牌资源库", headers, rows)]), "品牌资源库.xlsx")


@router.get("/projects.xlsx")
def export_projects(type: str | None = None, status: str | None = None,
                    db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(Project).options(joinedload(Project.location)).filter(
        Project.is_deleted.is_(False))
    if type:
        query = query.filter(Project.project_type == type)
    if status:
        query = query.filter(Project.project_status == status)
    projects = query.order_by(Project.project_code).all()
    headers = ["项目编码", "项目名称", "类型", "状态", "省", "市", "区", "地址",
               "经度", "纬度", "定位状态", "商业面积", "运营方", "合作意愿", "评分等级"]
    rows = []
    for p in projects:
        loc = p.location
        rows.append([p.project_code, p.project_name, p.project_type, p.project_status,
                     loc.province if loc else None, loc.city if loc else None,
                     loc.district if loc else None, loc.address if loc else None,
                     loc.longitude if loc else None, loc.latitude if loc else None,
                     loc.geocoding_status if loc else None, p.business_area_m2,
                     p.operator, p.cooperation_will, p.grade])
    return _xlsx_response(build_xlsx([("项目资源库", headers, rows)]), "项目资源库.xlsx")


@router.get("/projects/{project_id}/report.xlsx")
def export_project_report(project_id: int, db: Session = Depends(get_db),
                          _=Depends(get_current_user)):
    p = _load_project(db, project_id)
    return _xlsx_response(build_xlsx(_report_sections(db, p)),
                          f"{p.project_name}-招商报告.xlsx")


@router.get("/projects/{project_id}/report.pdf")
def export_project_report_pdf(project_id: int, db: Session = Depends(get_db),
                              _=Depends(get_current_user)):
    p = _load_project(db, project_id)
    pdf = build_report_pdf(f"{p.project_name} · 招商报告", _report_sections(db, p))
    return _download(pdf, f"{p.project_name}-招商报告.pdf", _PDF)


def _load_project(db: Session, project_id: int) -> Project:
    p = db.query(Project).options(joinedload(Project.location)).filter(
        Project.id == project_id, Project.is_deleted.is_(False)).first()
    if not p:
        raise HTTPException(404, "项目不存在")
    return p


def _report_sections(db: Session, p: Project) -> list[tuple[str, list, list]]:
    """组装招商报告的四个章节（xlsx / pdf 共用）。"""
    loc = p.location

    # 概况
    overview = [["项目编码", p.project_code], ["项目名称", p.project_name],
                ["类型", p.project_type], ["状态", p.project_status],
                ["城市", loc.city if loc else None], ["地址", loc.address if loc else None],
                ["商业面积(㎡)", p.business_area_m2], ["目标业态", p.target_formats],
                ["核心客群", p.core_customers], ["运营方", p.operator],
                ["招商阶段", p.leasing_stage], ["合作意愿", p.cooperation_will],
                ["评分等级", p.grade]]

    # 评分（当前）
    sc = db.query(ProjectScore).filter(ProjectScore.project_id == p.id,
                                       ProjectScore.is_current.is_(True)).first()
    score_rows = []
    if sc:
        labels = ["区位与交通", "体量与商业条件", "定位与客群质量", "运营与资源能力", "合作机会与推进意愿"]
        vals = [sc.score_location_traffic, sc.score_scale_condition,
                sc.score_positioning_customer, sc.score_operation_resource,
                sc.score_cooperation_opportunity]
        score_rows = [[l, v] for l, v in zip(labels, vals)]
        score_rows.append(["合计", sc.total_score])
        score_rows.append(["等级", sc.grade])

    # 推荐品牌（按规则实时计算，只读不落库）
    brands = db.query(Brand).options(joinedload(Brand.expansion)).filter(
        Brand.is_deleted.is_(False)).all()
    results = []
    for b in brands:
        r = matching.compute(b, p)
        results.append((b, r.weighted_score or 0, r.match_grade,
                        r.data_coverage_rate, r.hard_gate_triggered))
    results.sort(key=lambda x: x[1], reverse=True)
    rec_headers = ["品牌编码", "品牌名称", "综合分", "匹配等级", "资料覆盖率%", "硬门槛"]
    rec_rows = [[b.brand_code, b.brand_name, score, grade, cov, "是" if gate else "否"]
                for b, score, grade, cov, gate in results]

    # 候选清单
    lists = db.query(CandidateList).filter(
        CandidateList.target_project_id == p.id).all()
    cand_headers = ["候选清单", "品牌", "状态", "备注"]
    cand_rows = []
    for cl in lists:
        for it in cl.items:
            cand_rows.append([cl.list_name, it.brand.brand_name if it.brand else it.brand_id,
                              it.item_status, it.note])

    return [("项目概况", ["字段", "值"], overview),
            ("项目评分", ["维度", "得分"], score_rows or [["（暂无评分）", ""]]),
            ("推荐品牌", rec_headers, rec_rows),
            ("候选清单", cand_headers, cand_rows or [["（暂无候选）", "", "", ""]])]
