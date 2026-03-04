from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable
import os

from fpdf import FPDF

from ..models import Deliverable, Project


class SimplePDF(FPDF):
    def __init__(self, base_font: str = "Helvetica"):
        super().__init__()
        self.base_font = base_font

    def header(self):
        self.set_font(self.base_font, "B", 12)
        self.cell(0, 10, "Project Report", ln=True, align="L")
        self.ln(2)


EXTERNAL_FIELDS = [
    ("code", "Project Code"),
    ("name", "Name"),
    ("region", "Region"),
    ("asset_type", "Asset Type"),
    ("client_name", "Client"),
    ("address", "Address"),
    ("area_m2", "Area (m2)"),
    ("population_index", "Population Index"),
    ("current_stage", "Current Stage"),
]

INTERNAL_FIELDS = EXTERNAL_FIELDS + [
    ("external_enabled", "External Enabled"),
]


def _resolve_font_path() -> str | None:
    env_path = os.getenv("PDF_FONT_PATH")
    if env_path and Path(env_path).exists():
        return env_path
    candidates = [
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:\\\\Windows\\\\Fonts\\\\msyh.ttc",
        "C:\\\\Windows\\\\Fonts\\\\simsun.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    return None


def _configure_font(pdf: FPDF) -> str | None:
    font_path = _resolve_font_path()
    if font_path:
        pdf.add_font("Custom", "", font_path, uni=True)
        return "Custom"
    return None


def _safe_text(text: str) -> str:
    try:
        text.encode("latin-1")
        return text
    except UnicodeEncodeError:
        return text.encode("latin-1", "ignore").decode("latin-1")


def _needs_unicode(text: str) -> bool:
    return any(ord(ch) > 127 for ch in text)


def _set_font_for_text(pdf: FPDF, unicode_font: str | None, text: str, size: int, bold: bool = False) -> str:
    if unicode_font and _needs_unicode(text):
        pdf.set_font(unicode_font, "", size)
        return text
    pdf.set_font("Helvetica", "B" if bold else "", size)
    return _safe_text(text)


def generate_project_pdf(
    project: Project,
    deliverables: Iterable[Deliverable],
    audience: str,
    output_path: Path,
) -> None:
    pdf = SimplePDF(base_font="Helvetica")
    pdf.set_auto_page_break(auto=True, margin=15)
    unicode_font = _configure_font(pdf)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)

    fields = INTERNAL_FIELDS if audience == "internal" else EXTERNAL_FIELDS
    pdf.cell(0, 8, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.ln(2)

    for key, label in fields:
        value = getattr(project, key)
        text = f"{label}: {value if value is not None else '-'}"
        rendered = _set_font_for_text(pdf, unicode_font, text, size=10)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, rendered)

    if audience == "external" and project.external_summary:
        pdf.ln(2)
        heading = _set_font_for_text(pdf, unicode_font, "External Summary", size=10, bold=True)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 6, heading, ln=True)
        summary = project.external_summary
        summary_text = _set_font_for_text(pdf, unicode_font, summary, size=10)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 6, summary_text)

    pdf.ln(2)
    heading = _set_font_for_text(pdf, unicode_font, "Deliverables", size=10, bold=True)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 6, heading, ln=True)

    for item in deliverables:
        if audience == "external" and not item.is_external_visible:
            continue
        line = f"- {item.type} | {item.title} | v{item.version}"
        rendered = _set_font_for_text(pdf, unicode_font, line, size=10)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 6, rendered, ln=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
