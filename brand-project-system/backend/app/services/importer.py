"""Excel 一键导入管线：校验(dry-run) → 错误清单 → 入库(幂等+geocode) → 可回滚。

对齐系统框架三章：空串转 null；source_system+source_record_id 幂等；
错误定位到 sheet/行/字段/原值/建议；导入后对缺坐标项目解析，失败入错误清单。
一期覆盖两张主数据表（品牌档案 / 项目档案），其余 sheet 按同一规范扩展。
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from sqlalchemy.orm import Session

from ..models import Brand, Dictionary, Project, ProjectLocation
from .geocoding import apply_geocode, geocode_address

IMPORT_SOURCE = "excel_import"

# sheet 规格：如何在工作簿里定位、必填、枚举校验、字段映射（表头→模型属性）
SHEET_SPECS = {
    "brands": {
        "match": "品牌档案", "code": "brand_code",
        "required": ["brand_code", "brand_name", "l1_业态"],
        "enum": {},
        "map": {"brand_code": "brand_code", "brand_name": "brand_name",
                "brand_short_name": "brand_short_name", "l1_业态": "l1_category",
                "l2_业种": "l2_category", "tags": "tags",
                "operating_status": "operating_status", "hq_city": "hq_city",
                "brand_intro": "brand_intro"},
    },
    "projects": {
        "match": "项目档案", "code": "project_code",
        "required": ["project_code", "project_name", "project_type", "project_status",
                     "province", "city", "district", "address"],
        "enum": {"project_type": "project_type", "project_status": "project_status"},
        "map": {"project_code": "project_code", "project_name": "project_name",
                "project_short_name": "project_short_name", "project_type": "project_type",
                "project_status": "project_status", "operator": "operator",
                "asset_holder": "asset_holder"},
        "loc": ["province", "city", "district", "address"],
    },
}


@dataclass
class RowError:
    sheet: str
    row: int
    field: str
    value: str
    suggestion: str


@dataclass
class EntityReport:
    total: int = 0
    valid: int = 0
    error: int = 0
    to_update: int = 0


@dataclass
class ImportReport:
    summary: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    geocode_failed: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "summary": {k: asdict(v) for k, v in self.summary.items()},
            "errors": [asdict(e) for e in self.errors],
            "geocode_failed": self.geocode_failed,
        }


def _norm(v) -> str | None:
    """空串/纯空白 → None（校验前统一）。"""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _find_sheet(wb, keyword: str):
    for ws in wb.worksheets:
        if keyword in ws.title:
            return ws
    return None


def _read_rows(ws, code_field: str) -> tuple[list[str], list[tuple[int, dict]]]:
    """定位表头行（含 code_field 的行），返回 (headers, [(row_no, {header:value})])。"""
    header_row_idx, headers = None, []
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=4, values_only=True), 1):
        vals = [(_norm(c) or "") for c in row]
        if code_field in vals:
            header_row_idx, headers = i, vals
            break
    if header_row_idx is None:
        return [], []
    rows = []
    for r in range(header_row_idx + 1, ws.max_row + 1):
        cells = [ws.cell(r, c + 1).value for c in range(len(headers))]
        if all(_norm(c) is None for c in cells):
            continue
        rows.append((r, {h: _norm(v) for h, v in zip(headers, cells) if h}))
    return headers, rows


def _enum_labels(db: Session, dict_type: str) -> set[str]:
    q = db.query(Dictionary.label, Dictionary.code).filter(Dictionary.dict_type == dict_type)
    out: set[str] = set()
    for label, code in q.all():
        out.add(label)
        out.add(code)
    return out


def validate(wb, db: Session) -> tuple[ImportReport, dict]:
    """校验工作簿，返回 (报告, {entity: [合法行 dict]})。"""
    report = ImportReport()
    parsed: dict[str, list[dict]] = {}

    for entity, spec in SHEET_SPECS.items():
        ws = _find_sheet(wb, spec["match"])
        rep = EntityReport()
        parsed[entity] = []
        report.summary[entity] = rep
        if ws is None:
            continue
        _, rows = _read_rows(ws, spec["code"])
        enum_sets = {f: _enum_labels(db, dt) for f, dt in spec["enum"].items()}
        seen_codes: set[str] = set()
        existing = {c for (c,) in db.query(getattr(_model(entity), spec["code"])).all()}

        for row_no, data in rows:
            rep.total += 1
            row_errors = []
            # 必填
            for f in spec["required"]:
                if not data.get(f):
                    row_errors.append(RowError(ws.title, row_no, f, "", "必填，不能为空"))
            # 枚举
            for f, allowed in enum_sets.items():
                v = data.get(f)
                if v and v not in allowed:
                    row_errors.append(RowError(ws.title, row_no, f, v,
                                               f"须为字典 {spec['enum'][f]} 取值"))
            # 文件内重复
            code = data.get(spec["code"])
            if code:
                if code in seen_codes:
                    row_errors.append(RowError(ws.title, row_no, spec["code"], code,
                                               "文件内编码重复"))
                seen_codes.add(code)

            if row_errors:
                rep.error += 1
                report.errors.extend(row_errors)
            else:
                rep.valid += 1
                if code in existing:
                    rep.to_update += 1
                parsed[entity].append({"_row": row_no, **data})

    return report, parsed


def _model(entity: str):
    return {"brands": Brand, "projects": Project}[entity]


def commit(parsed: dict, db: Session, report: ImportReport) -> None:
    """把合法行入库（幂等 upsert + 项目 geocode）。异常则由调用方回滚。"""
    for entity, rows in parsed.items():
        spec = SHEET_SPECS[entity]
        Model = _model(entity)
        for data in rows:
            code = data[spec["code"]]
            obj = db.query(Model).filter(getattr(Model, spec["code"]) == code).first()
            if obj is None:
                obj = Model(**{spec["code"]: code}, source_system=IMPORT_SOURCE,
                            source_record_id=code)
                db.add(obj)
            for header, attr in spec["map"].items():
                if header in data and data[header] is not None:
                    setattr(obj, attr, data[header])
            db.flush()

            if entity == "projects":
                _upsert_location(db, obj, data, report)


def _upsert_location(db: Session, project, data: dict, report: ImportReport) -> None:
    loc = project.location or ProjectLocation(project_id=project.id)
    loc.province, loc.city = data.get("province"), data.get("city")
    loc.district, loc.address = data.get("district"), data.get("address")
    if loc.id is None:
        db.add(loc)
    result = geocode_address(loc.address, loc.city)
    apply_geocode(loc, result)
    if not result.ok:
        report.geocode_failed.append({
            "project_code": data.get("project_code"), "project_name": data.get("project_name"),
            "address": loc.address, "reason": "地址解析失败，需人工补坐标",
        })
