"""数据导出 单元 + 集成测试。"""
from __future__ import annotations

import io

import openpyxl

from app.services.exporter import build_xlsx


def _load(content: bytes):
    return openpyxl.load_workbook(io.BytesIO(content))


# ---------- 单元：构建器 ----------

def test_build_xlsx_sheets_and_cells():
    data = build_xlsx([("品牌", ["编码", "名称"], [["B-1", "迪卡侬"], ["B-2", "海底捞"]])])
    wb = _load(data)
    assert wb.sheetnames == ["品牌"]
    ws = wb["品牌"]
    assert [c.value for c in ws[1]] == ["编码", "名称"]
    assert ws.cell(2, 2).value == "迪卡侬"
    assert ws.freeze_panes == "A2"


def test_build_xlsx_truncates_long_sheet_name():
    long = "x" * 40
    wb = _load(build_xlsx([(long, ["a"], [[1]])]))
    assert len(wb.sheetnames[0]) == 31


# ---------- 集成：导出接口 ----------

def test_export_brands_xlsx(client, auth):
    r = client.get("/api/v1/export/brands.xlsx", headers=auth)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert "filename*=UTF-8''" in r.headers["content-disposition"]
    wb = _load(r.content)
    names = [ws.cell(row, 2).value for ws in [wb["品牌资源库"]] for row in range(2, wb["品牌资源库"].max_row + 1)]
    assert "迪卡侬" in names


def test_export_projects_xlsx(client, auth):
    r = client.get("/api/v1/export/projects.xlsx", headers=auth)
    assert r.status_code == 200
    wb = _load(r.content)
    ws = wb["项目资源库"]
    codes = [ws.cell(row, 1).value for row in range(2, ws.max_row + 1)]
    assert "P-1" in codes


def test_export_project_report(client, auth):
    r = client.get("/api/v1/export/projects/1/report.xlsx", headers=auth)
    assert r.status_code == 200
    wb = _load(r.content)
    assert set(wb.sheetnames) == {"项目概况", "项目评分", "推荐品牌", "候选清单"}
    rec = wb["推荐品牌"]
    brand_names = [rec.cell(row, 2).value for row in range(2, rec.max_row + 1)]
    assert "迪卡侬" in brand_names


def test_export_report_404(client, auth):
    assert client.get("/api/v1/export/projects/9999/report.xlsx", headers=auth).status_code == 404


def test_export_project_report_pdf(client, auth):
    r = client.get("/api/v1/export/projects/1/report.pdf", headers=auth)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert "filename*=UTF-8''" in r.headers["content-disposition"]
    assert r.content[:5] == b"%PDF-"          # PDF 魔数
    assert len(r.content) > 1500              # 非空报告


def test_export_report_pdf_404(client, auth):
    assert client.get("/api/v1/export/projects/9999/report.pdf", headers=auth).status_code == 404
