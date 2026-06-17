"""Convierte un Markdown a PDF usando reportlab.

Uso: python scripts/md_to_pdf.py docs/VALIDACION_REQUERIMIENTOS.md docs/VALIDACION_REQUERIMIENTOS.pdf
"""
import sys
import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, lightgrey, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT


def md_inline(text: str) -> str:
    """Convierte sintaxis inline de Markdown a HTML para Paragraph."""
    text = re.sub(r"`([^`]+)`", r'<font face="Courier" color="#5e2ca5">\1</font>', text)
    text = re.sub(r"\*\*([^\*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^\*]+)\*", r"<i>\1</i>", text)
    text = text.replace("✅", "&#10004;").replace("❌", "&#10008;")
    text = text.replace("⚠️", "&#9888;").replace("🚧", "&#128679;")
    text = text.replace("🔧", "&#128295;").replace("🔴", "&#128308;")
    text = text.replace("⭐", "&#11088;").replace("⚡", "&#9889;")
    text = text.replace("🟢", "&#128994;").replace("🟡", "&#128993;")
    return text


def parse_table(lines, i):
    """Parsea una tabla Markdown empezando en lines[i]."""
    header_line = lines[i]
    sep_line = lines[i + 1]
    if not re.match(r"^\s*\|?\s*[-:]+", sep_line):
        return None, i

    headers = [c.strip() for c in header_line.strip().strip("|").split("|")]
    rows = []
    j = i + 2
    while j < len(lines) and "|" in lines[j] and lines[j].strip():
        cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
        rows.append(cells)
        j += 1
    return (headers, rows), j


def build_doc(md_path: Path, out_path: Path):
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    styles = getSampleStyleSheet()
    purple = HexColor("#7c3aed")
    dark = HexColor("#111827")

    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=20, textColor=purple,
                       spaceAfter=12, spaceBefore=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=14, textColor=dark,
                       spaceAfter=8, spaceBefore=14, borderPadding=4)
    h3 = ParagraphStyle("h3", parent=styles["Heading3"], fontSize=11, textColor=purple,
                       spaceAfter=4, spaceBefore=10)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13,
                         alignment=TA_LEFT, spaceAfter=4)
    quote = ParagraphStyle("quote", parent=body, leftIndent=12, fontSize=9,
                          textColor=HexColor("#4b5563"), borderColor=lightgrey,
                          borderWidth=0, spaceBefore=4)
    code = ParagraphStyle("code", parent=body, fontName="Courier", fontSize=8,
                         backColor=HexColor("#f3f4f6"), textColor=dark,
                         leftIndent=8, rightIndent=8, leading=10)

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=md_path.stem.replace("_", " "),
    )
    story = []

    i = 0
    in_code_block = False
    code_buffer = []
    while i < len(lines):
        line = lines[i]

        # Code block fences
        if line.strip().startswith("```"):
            if in_code_block:
                story.append(Paragraph("<br/>".join(code_buffer), code))
                story.append(Spacer(1, 6))
                code_buffer = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue
        if in_code_block:
            esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            code_buffer.append(esc or "&nbsp;")
            i += 1
            continue

        # Headings
        if line.startswith("# "):
            story.append(Paragraph(md_inline(line[2:]), h1))
            i += 1
            continue
        if line.startswith("## "):
            story.append(Paragraph(md_inline(line[3:]), h2))
            i += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(md_inline(line[4:]), h3))
            i += 1
            continue
        if line.startswith("#### "):
            story.append(Paragraph(md_inline(line[5:]), h3))
            i += 1
            continue

        # Tables
        if "|" in line and i + 1 < len(lines) and re.match(r"^\s*\|?\s*[-:]+", lines[i + 1]):
            tbl, new_i = parse_table(lines, i)
            if tbl:
                headers, rows = tbl
                data = [[Paragraph(md_inline(h), body) for h in headers]]
                for r in rows:
                    # pad shorter rows
                    while len(r) < len(headers):
                        r.append("")
                    data.append([Paragraph(md_inline(c), body) for c in r])
                col_count = len(headers)
                avail = A4[0] - 4 * cm
                col_w = [avail / col_count] * col_count
                t = Table(data, colWidths=col_w, hAlign="LEFT")
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), purple),
                    ("TEXTCOLOR", (0, 0), (-1, 0), white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f9fafb")]),
                    ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#e5e7eb")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, HexColor("#e5e7eb")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 8))
                i = new_i
                continue

        # Horizontal rule
        if re.match(r"^---+$", line.strip()):
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Quote
        if line.startswith(">"):
            story.append(Paragraph(md_inline(line.lstrip("> ")), quote))
            i += 1
            continue

        # List item
        if re.match(r"^\s*[-*]\s+", line):
            content = re.sub(r"^\s*[-*]\s+", "&#8226;&nbsp;&nbsp;", line)
            story.append(Paragraph(md_inline(content), body))
            i += 1
            continue

        # Regular paragraph
        if line.strip():
            story.append(Paragraph(md_inline(line), body))
        else:
            story.append(Spacer(1, 4))
        i += 1

    doc.build(story)
    print(f"PDF generado: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python md_to_pdf.py <input.md> <output.pdf>")
        sys.exit(1)
    build_doc(Path(sys.argv[1]), Path(sys.argv[2]))
