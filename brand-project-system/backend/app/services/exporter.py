"""Excel 导出：通用多 sheet 构建器（纯格式化，不碰 DB，便于测试）。"""
from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# 一个 sheet = (名称, 表头, 行数据)
SheetSpec = tuple[str, list[str], list[list]]

_HDR_FILL = PatternFill("solid", fgColor="0E766E")
_HDR_FONT = Font(name="PingFang SC", color="FFFFFF", bold=True, size=10)
_CELL_FONT = Font(name="PingFang SC", size=10)
_MAX_W = 48


def _autowidth(ws, headers: list[str], rows: list[list]) -> None:
    for c, h in enumerate(headers, 1):
        longest = len(str(h))
        for row in rows:
            if c <= len(row) and row[c - 1] is not None:
                longest = max(longest, len(str(row[c - 1])))
        ws.column_dimensions[get_column_letter(c)].width = min(longest + 2, _MAX_W)


def build_xlsx(sheets: list[SheetSpec]) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    for name, headers, rows in sheets:
        ws = wb.create_sheet(name[:31] or "Sheet")   # Excel sheet 名≤31 字符
        for c, h in enumerate(headers, 1):
            cell = ws.cell(1, c, h)
            cell.fill = _HDR_FILL
            cell.font = _HDR_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for ri, row in enumerate(rows, 2):
            for c, v in enumerate(row, 1):
                cell = ws.cell(ri, c, v)
                cell.font = _CELL_FONT
                cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.freeze_panes = "A2"
        ws.row_dimensions[1].height = 26
        _autowidth(ws, headers, rows)
    if not wb.worksheets:
        wb.create_sheet("空")
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
