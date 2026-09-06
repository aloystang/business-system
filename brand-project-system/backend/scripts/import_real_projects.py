"""一次性导入新盛真实商业项目（源：新盛资产清单-分类.xlsx 的商业子集）。

坐标留空（geocoding_status=待定位），不编造；拿到高德 Web 服务 Key 后可批量补坐标。
按项目名去重（已存在则跳过），幂等：source_system=asset_list_v1 + source_record_id=项目名。
    python scripts/import_real_projects.py [xlsx路径]
"""
from __future__ import annotations

import sys

import openpyxl

from app.database import SessionLocal
from app.models import Project, ProjectLocation

SRC_DEFAULT = ("/Users/aloystang/Downloads/_已整理_2026-06-02/03_表格数据/"
               "新盛资产清单-分类.xlsx")
SHEETS = ["其他商业资产", "写字楼、场馆资产"]
SOURCE = "asset_list_v1"

# 业态 → 项目类型（系统字典口径）
TYPE_MAP = {
    "经营性场馆": "体育场馆商业", "写字楼": "写字楼或公寓配套",
    "商业": "商业街区", "其他-文化设施": "文旅商业", "其他": "其他",
}


def _clean(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _district(pos: str) -> str:
    if "渝中" in pos or "解放碑" in pos or "渝海" in pos:
        return "渝中区"
    return "两江新区"


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def run(path: str) -> None:
    wb = openpyxl.load_workbook(path, data_only=True)
    db = SessionLocal()
    imported = skipped = 0
    seq = 1
    try:
        existing_names = {n for (n,) in db.query(Project.project_name).all()}
        existing_codes = {c for (c,) in db.query(Project.project_code).all()}
        for sheet in SHEETS:
            ws = wb[sheet]
            for r in ws.iter_rows(min_row=3, max_row=ws.max_row, values_only=True):
                oper = _clean(r[1]) if len(r) > 1 else None
                name = _clean(r[3]) if len(r) > 3 else None
                fmt = _clean(r[4]) if len(r) > 4 else None
                area = _num(r[5]) if len(r) > 5 else None
                pos = _clean(r[6]) if len(r) > 6 else None
                holder = _clean(r[2]) if len(r) > 2 else None
                if not name or name in ("合计", "小计", "项目名称") or "土储" in name:
                    continue
                if not oper or "新盛" not in oper:
                    continue
                if name in existing_names:      # 去重
                    skipped += 1
                    continue
                # 生成唯一编码
                while f"XS-A-{seq:03d}" in existing_codes:
                    seq += 1
                code = f"XS-A-{seq:03d}"
                existing_codes.add(code)
                seq += 1

                ptype = TYPE_MAP.get(fmt or "", "其他")
                p = Project(
                    project_code=code, project_name=name, project_type=ptype,
                    project_status="招商中", business_area_m2=area,
                    leasable_area_m2=area, asset_holder=holder, operator=oper,
                    source_system=SOURCE, source_record_id=name,
                )
                db.add(p)
                db.flush()
                db.add(ProjectLocation(
                    project_id=p.id, province="重庆市", city="重庆市",
                    district=_district(pos or ""), address=pos or name,
                    geocoding_status="待定位"))
                existing_names.add(name)
                imported += 1
        db.commit()
        total = db.query(Project).filter(Project.is_deleted.is_(False)).count()
        print(f"✅ 导入完成：新增 {imported}，跳过(已存在) {skipped}。")
        print(f"   系统项目总数：{total}（坐标待定位，配好高德 Web Key 后批量补坐标即可上图）")
    finally:
        db.close()


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else SRC_DEFAULT)
