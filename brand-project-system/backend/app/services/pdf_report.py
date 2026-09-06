"""PDF 报告：用 reportlab + 内置 STSong-Light（中文）生成，无需外部字体/系统依赖。"""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_FONT = "STSong-Light"
_registered = False

# 一个 section = (标题, 表头, 行数据)
SectionSpec = tuple[str, list[str], list[list]]

_TEAL = colors.HexColor("#0E766E")


def _ensure_font() -> None:
    global _registered
    if not _registered:
        pdfmetrics.registerFont(UnicodeCIDFont(_FONT))
        _registered = True


def _style(name: str, size: int, bold: bool = False, color=colors.black) -> ParagraphStyle:
    return ParagraphStyle(name, fontName=_FONT, fontSize=size, leading=size + 4,
                          textColor=color, spaceAfter=4)


def build_report_pdf(title: str, sections: list[SectionSpec]) -> bytes:
    _ensure_font()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm, title=title)
    h1 = _style("h1", 18, color=_TEAL)
    h2 = _style("h2", 12, color=_TEAL)
    body = _style("body", 9)
    flow = [Paragraph(title, h1), Spacer(1, 6 * mm)]

    for heading, headers, rows in sections:
        flow.append(Paragraph(heading, h2))
        flow.append(Spacer(1, 2 * mm))
        data = [[Paragraph(str(h), _style("th", 9, color=colors.white)) for h in headers]]
        for row in rows:
            data.append([Paragraph("" if c is None else str(c), body) for c in row])
        tbl = Table(data, repeatRows=1, hAlign="LEFT")
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _TEAL),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C3CCD3")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F5F7")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        flow.append(tbl)
        flow.append(Spacer(1, 6 * mm))

    doc.build(flow)
    return buf.getvalue()
