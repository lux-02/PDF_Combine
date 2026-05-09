import io
import os
from typing import Optional

from PIL import Image

try:
    from docx import Document
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    DOCX_PARSER_SUPPORT = True
except ImportError:
    DOCX_PARSER_SUPPORT = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    REPORTLAB_SUPPORT = True
except ImportError:
    REPORTLAB_SUPPORT = False

DOCX_TEXT_SUPPORT = DOCX_PARSER_SUPPORT and REPORTLAB_SUPPORT


def find_korean_font_path() -> Optional[str]:
    candidates = [
        os.path.join(os.getcwd(), "fonts", "NanumGothic.ttf"),
        os.path.join(os.getcwd(), "fonts", "NanumGothic-Regular.ttf"),
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/Library/Fonts/AppleGothic.ttf",
        "/Library/Fonts/NanumGothic.ttf",
        "/Library/Fonts/NanumGothic-Regular.ttf",
        "/Library/Fonts/Malgun Gothic.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "C:\\Windows\\Fonts\\malgun.ttf",
        "C:\\Windows\\Fonts\\NanumGothic.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def image_to_pdf_bytes(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="PDF")
    buf.seek(0)
    return buf.read()


def iter_docx_blocks(document):
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def docx_to_pdf_simple(docx_bytes: bytes) -> tuple:
    """Returns (pdf_buffer, font_used, has_non_ascii)."""
    document = Document(io.BytesIO(docx_bytes))
    blocks = []
    for block in iter_docx_blocks(document):
        if hasattr(block, "text"):
            text = block.text.strip()
            blocks.append(text if text else "")
            continue
        rows = []
        for row in block.rows:
            cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
            rows.append(" | ".join(cells).strip())
        blocks.extend(rows)
        blocks.append("")

    buffer = io.BytesIO()
    page_width, page_height = A4
    margin_x = 40
    margin_y = 40
    max_width = page_width - (margin_x * 2)
    font_size = 11
    line_gap = font_size * 1.4

    font_name = "Helvetica"
    font_used = False
    font_path = find_korean_font_path()
    if font_path:
        try:
            if "DocxFont" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("DocxFont", font_path))
            font_name = "DocxFont"
            font_used = True
        except Exception:
            font_name = "Helvetica"
            font_used = False

    has_non_ascii = any(any(ord(ch) > 127 for ch in text) for text in blocks if text)

    def wrap_text(text):
        if not text:
            return [""]
        words = text.split()
        if not words:
            return [""]
        lines = []
        current = ""
        for word in words:
            test = word if not current else f"{current} {word}"
            if pdfmetrics.stringWidth(test, font_name, font_size) <= max_width:
                current = test
                continue
            if current:
                lines.append(current)
            if pdfmetrics.stringWidth(word, font_name, font_size) > max_width:
                chunk = ""
                for ch in word:
                    test_chunk = chunk + ch
                    if pdfmetrics.stringWidth(test_chunk, font_name, font_size) <= max_width:
                        chunk = test_chunk
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = ch
                current = chunk
            else:
                current = word
        if current:
            lines.append(current)
        return lines

    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    pdf_canvas.setFont(font_name, font_size)
    cursor_y = page_height - margin_y

    for block in blocks:
        for line in wrap_text(block):
            if cursor_y < margin_y:
                pdf_canvas.showPage()
                pdf_canvas.setFont(font_name, font_size)
                cursor_y = page_height - margin_y
            pdf_canvas.drawString(margin_x, cursor_y, line)
            cursor_y -= line_gap
        if block == "":
            cursor_y -= line_gap * 0.3

    pdf_canvas.save()
    buffer.seek(0)
    return buffer, font_used, has_non_ascii
