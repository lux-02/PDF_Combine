import html
import io
import math
import os
import re
import uuid

import fitz  # PyMuPDF
import streamlit as st
from PIL import Image
from pypdf import PdfReader, PdfWriter

try:
    from docx import Document

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
SUPPORTED_TYPES = ["pdf", "jpg", "jpeg", "png", "docx"]
THUMBNAIL_SCALE = 0.30
CANVAS_PAGE_SIZE = 12


st.set_page_config(
    page_title="PDF Page Studio",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap');

:root {
    --paper: #f5efe3;
    --panel: rgba(255, 252, 247, 0.78);
    --card: #fffdfa;
    --ink: #1d2930;
    --muted: #65747c;
    --accent: #0f766e;
    --accent-deep: #134e4a;
    --accent-soft: #e6f3f0;
    --signal: #c75d1f;
    --line: #d9d2c4;
    --shadow: 0 28px 80px rgba(28, 36, 39, 0.12);
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans KR', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.16), transparent 26%),
        radial-gradient(circle at top right, rgba(199, 93, 31, 0.12), transparent 24%),
        linear-gradient(180deg, #fbf8f2 0%, #f2ecdf 100%);
}

.block-container {
    max-width: 1320px;
    padding-top: 1.8rem;
    padding-bottom: 3rem;
}

.hero-panel {
    background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.88) 0%, rgba(249, 245, 237, 0.72) 100%);
    border: 1px solid rgba(217, 210, 196, 0.92);
    border-radius: 28px;
    box-shadow: var(--shadow);
    padding: 2rem 2.2rem;
    margin-bottom: 1.4rem;
}

.hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.5fr) minmax(260px, 0.85fr);
    gap: 1.25rem;
    align-items: stretch;
}

.eyebrow {
    margin: 0 0 0.6rem 0;
    color: var(--signal);
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.16em;
}

.hero-panel h1 {
    margin: 0;
    color: var(--ink);
    font-family: 'Fraunces', serif;
    font-size: clamp(2.2rem, 4vw, 3.8rem);
    line-height: 1.02;
}

.hero-panel p {
    margin: 1rem 0 0 0;
    color: var(--muted);
    font-size: 1.03rem;
    line-height: 1.68;
}

.hero-aside {
    background: rgba(15, 118, 110, 0.08);
    border: 1px solid rgba(15, 118, 110, 0.14);
    border-radius: 22px;
    padding: 1.1rem 1.2rem;
}

.hero-aside h3 {
    margin: 0 0 0.75rem 0;
    color: var(--ink);
    font-size: 1rem;
}

.hero-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.hero-pills span {
    background: rgba(255, 255, 255, 0.82);
    border: 1px solid rgba(15, 118, 110, 0.14);
    color: var(--accent-deep);
    border-radius: 999px;
    padding: 0.45rem 0.85rem;
    font-size: 0.88rem;
    font-weight: 600;
}

.section-title {
    margin: 1.25rem 0 0.75rem 0;
    color: var(--ink);
    font-family: 'Fraunces', serif;
    font-size: 1.6rem;
}

.section-kicker {
    color: var(--signal);
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    margin-bottom: 0.3rem;
}

.section-note {
    background: var(--accent-soft);
    border: 1px solid rgba(15, 118, 110, 0.14);
    color: var(--accent-deep);
    border-radius: 16px;
    padding: 0.75rem 0.9rem;
    font-size: 0.92rem;
    margin-bottom: 0.85rem;
}

.insert-banner {
    background: rgba(255, 249, 237, 0.96);
    border: 1px dashed rgba(199, 93, 31, 0.34);
    color: #8a4216;
    border-radius: 16px;
    padding: 0.75rem 0.9rem;
    font-size: 0.92rem;
    margin-bottom: 0.85rem;
}

.page-topline {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    align-items: center;
    margin-bottom: 0.55rem;
}

.page-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 3rem;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    background: rgba(15, 118, 110, 0.12);
    color: var(--accent-deep);
    font-weight: 700;
    font-size: 0.88rem;
}

.source-pill {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    background: rgba(29, 41, 48, 0.06);
    color: var(--muted);
    padding: 0.32rem 0.6rem;
    font-size: 0.74rem;
    font-weight: 600;
}

.page-meta {
    color: var(--ink);
    font-size: 0.93rem;
    font-weight: 600;
    line-height: 1.45;
    margin: 0.35rem 0 0.2rem 0;
}

.page-submeta {
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.45;
    margin-bottom: 0.6rem;
}

.empty-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.empty-card {
    background: rgba(255, 255, 255, 0.82);
    border: 1px solid rgba(217, 210, 196, 0.95);
    border-radius: 22px;
    padding: 1.35rem;
    min-height: 180px;
    box-shadow: 0 18px 44px rgba(28, 36, 39, 0.08);
}

.empty-card h3 {
    margin: 0.8rem 0 0.5rem 0;
    color: var(--ink);
    font-size: 1.08rem;
}

.empty-card p {
    margin: 0;
    color: var(--muted);
    font-size: 0.94rem;
    line-height: 1.6;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--panel);
    border: 1px solid rgba(217, 210, 196, 0.92);
    border-radius: 22px;
    box-shadow: 0 18px 48px rgba(28, 36, 39, 0.08);
}

div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(217, 210, 196, 0.92);
    border-radius: 18px;
    padding: 0.4rem;
}

div[data-testid="stMetricValue"] {
    color: var(--ink);
}

div[data-testid="stMetricLabel"] {
    color: var(--muted);
}

div[data-testid="stFileUploader"] {
    background: rgba(255, 255, 255, 0.72);
    border-radius: 18px;
}

.stButton > button {
    border-radius: 999px;
    border: 1px solid rgba(15, 118, 110, 0.1);
    background: #eef3f2;
    color: var(--ink);
    font-weight: 600;
    min-height: 2.8rem;
    transition: all 0.18s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(15, 118, 110, 0.28);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0f766e 0%, #134e4a 100%);
    color: white;
    box-shadow: 0 14px 28px rgba(15, 118, 110, 0.2);
}

.stTextInput > div > div > input,
.stNumberInput input {
    border-radius: 14px;
}

div[data-testid="stImage"] img {
    border-radius: 16px;
    border: 1px solid rgba(217, 210, 196, 0.8);
}

@media (max-width: 960px) {
    .hero-grid,
    .empty-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


def iter_docx_blocks(document):
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def find_korean_font_path():
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


def docx_to_pdf_simple(docx_bytes):
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


def image_to_pdf_bytes(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    buffer = io.BytesIO()
    image.save(buffer, format="PDF")
    buffer.seek(0)
    return buffer.getvalue()


def create_page_items(pdf_bytes, document_id, source_name, source_kind):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_items = []
    try:
        if doc.page_count == 0:
            raise ValueError("페이지가 없는 문서는 편집기에 추가할 수 없습니다.")

        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(
                matrix=fitz.Matrix(THUMBNAIL_SCALE, THUMBNAIL_SCALE),
                alpha=False,
            )
            page_items.append(
                {
                    "id": uuid.uuid4().hex,
                    "document_id": document_id,
                    "source_name": source_name,
                    "source_kind": source_kind,
                    "source_page_number": page_index + 1,
                    "source_total_pages": doc.page_count,
                    "thumbnail": pix.tobytes("png"),
                }
            )
    finally:
        doc.close()

    return page_items


def build_document_from_upload(uploaded_file):
    raw_bytes = uploaded_file.getvalue()
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    document_id = uuid.uuid4().hex
    notices = []

    if file_ext == ".pdf":
        pdf_bytes = raw_bytes
        source_kind = "PDF"
    elif file_ext == ".docx":
        if not DOCX_TEXT_SUPPORT:
            raise RuntimeError("DOCX 변환에 필요한 python-docx 또는 reportlab이 설치되어 있지 않습니다.")
        pdf_stream, font_used, has_non_ascii = docx_to_pdf_simple(raw_bytes)
        pdf_bytes = pdf_stream.getvalue()
        source_kind = "DOCX"
        if has_non_ascii and not font_used:
            notices.append(
                {
                    "level": "warning",
                    "text": (
                        f"{uploaded_file.name}: 한글 폰트를 찾지 못해 일부 글자가 깨질 수 있습니다. "
                        "fonts/NanumGothic.ttf 추가를 권장합니다."
                    ),
                }
            )
    elif file_ext in [".jpg", ".jpeg", ".png"]:
        pdf_bytes = image_to_pdf_bytes(raw_bytes)
        source_kind = "IMAGE"
    else:
        raise ValueError("지원하지 않는 파일 형식입니다.")

    page_items = create_page_items(
        pdf_bytes=pdf_bytes,
        document_id=document_id,
        source_name=uploaded_file.name,
        source_kind=source_kind,
    )

    document = {
        "id": document_id,
        "name": uploaded_file.name,
        "kind": source_kind,
        "pdf_bytes": pdf_bytes,
        "page_count": len(page_items),
    }
    return document, page_items, notices


def ensure_session_state():
    defaults = {
        "documents": {},
        "page_items": [],
        "selected_page_ids": set(),
        "uploader_key": 0,
        "insert_position": 0,
        "canvas_page": 1,
        "move_target_position_state": 1,
        "move_target_position_input": 1,
        "output_pdf_bytes": None,
        "export_filename": "edited_output.pdf",
        "notices": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def invalidate_output():
    st.session_state.output_pdf_bytes = None


def refresh_uploader():
    st.session_state.uploader_key += 1


def set_notices(notices):
    st.session_state.notices = notices


def prune_unused_documents():
    active_document_ids = {page["document_id"] for page in st.session_state.page_items}
    st.session_state.documents = {
        doc_id: document
        for doc_id, document in st.session_state.documents.items()
        if doc_id in active_document_ids
    }


def clear_selection():
    for page_id in list(st.session_state.selected_page_ids):
        widget_key = f"select_{page_id}"
        if widget_key in st.session_state:
            st.session_state[widget_key] = False
    st.session_state.selected_page_ids = set()


def select_page_ids(page_ids):
    for page_id in page_ids:
        widget_key = f"select_{page_id}"
        if widget_key in st.session_state:
            st.session_state[widget_key] = True
    st.session_state.selected_page_ids.update(page_ids)


def get_selected_page_ids_in_order():
    selected_lookup = st.session_state.selected_page_ids
    return [
        page["id"]
        for page in st.session_state.page_items
        if page["id"] in selected_lookup
    ]


def hydrate_selection_from_widgets():
    selected_page_ids = set(st.session_state.selected_page_ids)
    current_page_ids = {page["id"] for page in st.session_state.page_items}

    for page in st.session_state.page_items:
        widget_key = f"select_{page['id']}"
        if widget_key not in st.session_state:
            continue
        if st.session_state[widget_key]:
            selected_page_ids.add(page["id"])
        else:
            selected_page_ids.discard(page["id"])

    st.session_state.selected_page_ids = {
        page_id for page_id in selected_page_ids if page_id in current_page_ids
    }


def clamp_editor_state():
    total_pages = len(st.session_state.page_items)
    current_page_ids = {page["id"] for page in st.session_state.page_items}
    st.session_state.selected_page_ids = {
        page_id
        for page_id in st.session_state.selected_page_ids
        if page_id in current_page_ids
    }

    st.session_state.insert_position = max(0, min(st.session_state.insert_position, total_pages))

    max_canvas_page = max(1, math.ceil(total_pages / CANVAS_PAGE_SIZE)) if total_pages else 1
    st.session_state.canvas_page = max(1, min(st.session_state.canvas_page, max_canvas_page))

    remaining_slots = max(1, total_pages - len(get_selected_page_ids_in_order()) + 1)
    st.session_state.move_target_position_state = max(
        1,
        min(st.session_state.move_target_position_state, remaining_slots),
    )


def jump_canvas_to_index(index):
    st.session_state.canvas_page = max(1, (index // CANVAS_PAGE_SIZE) + 1)


def describe_insert_position():
    page_items = st.session_state.page_items
    insert_position = st.session_state.insert_position

    if not page_items:
        return "첫 문서를 올리면 모든 페이지가 바로 편집 캔버스로 펼쳐집니다."
    if insert_position <= 0:
        return "다음 업로드는 문서 맨 앞에 삽입됩니다."
    if insert_position >= len(page_items):
        return "다음 업로드는 문서 맨 뒤에 이어 붙습니다."

    prev_page = page_items[insert_position - 1]
    return (
        f"다음 업로드는 {insert_position}번 페이지 뒤에 삽입됩니다. "
        f"({html.escape(prev_page['source_name'])} · 원본 {prev_page['source_page_number']}페이지 뒤)"
    )


def reset_editor():
    clear_selection()
    st.session_state.documents = {}
    st.session_state.page_items = []
    st.session_state.insert_position = 0
    st.session_state.canvas_page = 1
    st.session_state.move_target_position_state = 1
    st.session_state.move_target_position_input = 1
    st.session_state.output_pdf_bytes = None
    st.session_state.export_filename = "edited_output.pdf"
    set_notices([])
    refresh_uploader()


def add_documents_to_canvas(uploaded_files):
    insertion_index = st.session_state.insert_position
    new_documents = {}
    new_pages = []
    notices = []
    success_documents = 0

    for uploaded_file in uploaded_files:
        try:
            document, page_items, doc_notices = build_document_from_upload(uploaded_file)
            new_documents[document["id"]] = document
            new_pages.extend(page_items)
            notices.extend(doc_notices)
            success_documents += 1
        except Exception as exc:
            notices.append({"level": "error", "text": f"{uploaded_file.name}: {exc}"})

    if success_documents == 0:
        set_notices(notices)
        return

    st.session_state.documents.update(new_documents)
    st.session_state.page_items[insertion_index:insertion_index] = new_pages
    st.session_state.insert_position = insertion_index + len(new_pages)
    jump_canvas_to_index(insertion_index)
    invalidate_output()

    notices.insert(
        0,
        {
            "level": "info",
            "text": (
                f"{success_documents}개 문서를 편집 캔버스에 추가했습니다. "
                f"새로 들어간 페이지는 총 {len(new_pages)}장입니다."
            ),
        },
    )
    set_notices(notices)
    clamp_editor_state()


def move_selected_pages(target_position):
    selected_ids = get_selected_page_ids_in_order()
    if not selected_ids:
        return False

    moved_pages = []
    remaining_pages = []
    selected_lookup = set(selected_ids)
    for page in st.session_state.page_items:
        if page["id"] in selected_lookup:
            moved_pages.append(page)
        else:
            remaining_pages.append(page)

    target_index = max(0, min(target_position, len(remaining_pages)))
    st.session_state.page_items = (
        remaining_pages[:target_index] + moved_pages + remaining_pages[target_index:]
    )
    st.session_state.insert_position = target_index + len(moved_pages)
    jump_canvas_to_index(target_index)
    invalidate_output()
    clamp_editor_state()
    return True


def move_single_page(page_id, direction):
    page_items = st.session_state.page_items
    current_index = next(
        (index for index, page in enumerate(page_items) if page["id"] == page_id),
        None,
    )
    if current_index is None:
        return False

    target_index = current_index + direction
    if target_index < 0 or target_index >= len(page_items):
        return False

    page = page_items.pop(current_index)
    page_items.insert(target_index, page)
    st.session_state.page_items = page_items
    st.session_state.insert_position = target_index + 1
    jump_canvas_to_index(target_index)
    invalidate_output()
    clamp_editor_state()
    return True


def natural_sort_key(value):
    parts = re.split(r"(\d+)", value.casefold())
    return [int(part) if part.isdigit() else part for part in parts]


def sort_page_items_by_source(reverse=False):
    grouped_pages = {}
    document_order = []

    for page in st.session_state.page_items:
        document_id = page["document_id"]
        if document_id not in grouped_pages:
            grouped_pages[document_id] = []
            document_order.append(document_id)
        grouped_pages[document_id].append(page)

    sorted_document_ids = sorted(
        document_order,
        key=lambda document_id: natural_sort_key(grouped_pages[document_id][0]["source_name"]),
        reverse=reverse,
    )

    sorted_pages = []
    for document_id in sorted_document_ids:
        pages = sorted(
            grouped_pages[document_id],
            key=lambda page: page["source_page_number"],
        )
        sorted_pages.extend(pages)

    st.session_state.page_items = sorted_pages
    st.session_state.canvas_page = 1
    invalidate_output()
    clamp_editor_state()


def remove_pages_by_ids(page_ids):
    page_ids = set(page_ids)
    if not page_ids:
        return False

    st.session_state.page_items = [
        page for page in st.session_state.page_items if page["id"] not in page_ids
    ]
    st.session_state.selected_page_ids.difference_update(page_ids)
    for page_id in page_ids:
        widget_key = f"select_{page_id}"
        if widget_key in st.session_state:
            st.session_state[widget_key] = False

    prune_unused_documents()
    invalidate_output()
    clamp_editor_state()
    return True


def set_insert_position(position):
    st.session_state.insert_position = position
    clamp_editor_state()


def build_output_pdf():
    writer = PdfWriter()
    reader_cache = {}
    try:
        for page in st.session_state.page_items:
            document_id = page["document_id"]
            if document_id not in reader_cache:
                document = st.session_state.documents[document_id]
                reader_cache[document_id] = PdfReader(io.BytesIO(document["pdf_bytes"]))
            reader = reader_cache[document_id]
            writer.add_page(reader.pages[page["source_page_number"] - 1])

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        return output_stream.getvalue()
    finally:
        writer.close()


def show_notices():
    for notice in st.session_state.notices:
        level = notice.get("level", "info")
        message = notice.get("text", "")
        if level == "warning":
            st.warning(message)
        elif level == "error":
            st.error(message)
        else:
            st.info(message)


def render_source_summary():
    active_document_ids = []
    seen = set()
    for page in st.session_state.page_items:
        document_id = page["document_id"]
        if document_id in seen:
            continue
        seen.add(document_id)
        active_document_ids.append(document_id)

    with st.expander("현재 소스 문서 보기", expanded=False):
        for document_id in active_document_ids:
            document = st.session_state.documents[document_id]
            active_pages = sum(
                1 for page in st.session_state.page_items if page["document_id"] == document_id
            )
            st.markdown(
                f"- **{document['name']}** · {document['kind']} · 현재 사용 중 {active_pages}장"
            )


ensure_session_state()
hydrate_selection_from_widgets()
clamp_editor_state()

st.markdown(
    """
<section class="hero-panel">
    <p class="eyebrow">PDF PAGE STUDIO</p>
    <div class="hero-grid">
        <div>
            <h1>페이지 단위로 재배열하는 PDF 작업대</h1>
            <p>
                업로드한 문서를 페이지 카드로 펼친 뒤, 원하는 페이지를 선택해서 한 번에 이동하고,
                필요 없는 장은 바로 지우고, 다른 PDF는 중간 위치에 끼워 넣은 뒤 다시 저장합니다.
            </p>
        </div>
        <div class="hero-aside">
            <h3>새 편집 흐름</h3>
            <div class="hero-pills">
                <span>페이지 썸네일 캔버스</span>
                <span>선택 후 배치 이동</span>
                <span>삽입 위치 커서</span>
                <span>즉시 삭제</span>
            </div>
        </div>
    </div>
</section>
""",
    unsafe_allow_html=True,
)

show_notices()

total_pages = len(st.session_state.page_items)
selected_count = len(get_selected_page_ids_in_order())
active_document_count = len({page["document_id"] for page in st.session_state.page_items})

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
with metric_col1:
    st.metric("활성 문서", f"{active_document_count}개")
with metric_col2:
    st.metric("편집 페이지", f"{total_pages}장")
with metric_col3:
    st.metric("선택 페이지", f"{selected_count}장")
with metric_col4:
    st.metric("다음 삽입 슬롯", f"{st.session_state.insert_position + 1}")

st.markdown('<div class="section-kicker">INTAKE</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">소스 문서 추가</div>', unsafe_allow_html=True)

with st.container(border=True):
    info_col, action_col1, action_col2, action_col3 = st.columns([3, 1, 1, 1])
    with info_col:
        st.markdown(
            f'<div class="section-note">{describe_insert_position()}</div>',
            unsafe_allow_html=True,
        )
    with action_col1:
        if st.button("맨 앞 삽입", use_container_width=True, disabled=not total_pages):
            set_insert_position(0)
            st.rerun()
    with action_col2:
        if st.button("맨 뒤 삽입", use_container_width=True, disabled=not total_pages):
            set_insert_position(total_pages)
            st.rerun()
    with action_col3:
        if st.button("캔버스 비우기", use_container_width=True, disabled=not total_pages):
            reset_editor()
            st.rerun()

    uploaded_files = st.file_uploader(
        "PDF, 이미지, DOCX를 선택하세요",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}",
        help="업로드 후 현재 삽입 위치 기준으로 페이지가 편집 캔버스에 추가됩니다.",
    )

    upload_col1, upload_col2 = st.columns([2, 1])
    with upload_col1:
        if uploaded_files:
            st.caption(
                f"{len(uploaded_files)}개 문서가 준비되었습니다. 버튼을 누르면 현재 삽입 위치에 추가됩니다."
            )
        else:
            st.caption("PDF는 페이지별로 분해되고, 이미지와 DOCX도 PDF 페이지로 변환되어 같은 방식으로 편집됩니다.")
    with upload_col2:
        add_disabled = not uploaded_files
        if st.button("현재 위치에 문서 추가", type="primary", use_container_width=True, disabled=add_disabled):
            with st.spinner("문서를 페이지 편집 캔버스로 펼치는 중입니다..."):
                add_documents_to_canvas(uploaded_files)
            refresh_uploader()
            st.rerun()

if not total_pages:
    st.markdown(
        """
<div class="empty-grid">
    <div class="empty-card">
        <div style="font-size: 2.2rem;">1</div>
        <h3>문서를 펼칩니다</h3>
        <p>업로드한 PDF를 페이지 단위 카드로 풀어내서 전체 순서를 한눈에 볼 수 있게 만듭니다.</p>
    </div>
    <div class="empty-card">
        <div style="font-size: 2.2rem;">2</div>
        <h3>선택해서 이동합니다</h3>
        <p>드래그만 강요하지 않고, 여러 페이지를 선택한 뒤 원하는 시작 위치 번호로 한 번에 이동시킵니다.</p>
    </div>
    <div class="empty-card">
        <div style="font-size: 2.2rem;">3</div>
        <h3>중간 삽입 후 저장합니다</h3>
        <p>특정 페이지 뒤를 삽입 위치로 지정하고 다른 문서를 추가한 다음, 새 PDF로 다시 저장합니다.</p>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    render_source_summary()

    st.markdown('<div class="section-kicker">EDITOR</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">페이지 캔버스</div>', unsafe_allow_html=True)

    with st.container(border=True):
        total_canvas_pages = max(1, math.ceil(total_pages / CANVAS_PAGE_SIZE))
        st.session_state.canvas_page = max(1, min(st.session_state.canvas_page, total_canvas_pages))
        canvas_start = (st.session_state.canvas_page - 1) * CANVAS_PAGE_SIZE
        canvas_end = min(canvas_start + CANVAS_PAGE_SIZE, total_pages)
        visible_pages = st.session_state.page_items[canvas_start:canvas_end]

        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 2, 2])
        with nav_col1:
            if st.button("이전 묶음", use_container_width=True, disabled=st.session_state.canvas_page == 1):
                st.session_state.canvas_page -= 1
                st.rerun()
        with nav_col2:
            if st.button(
                "다음 묶음",
                use_container_width=True,
                disabled=st.session_state.canvas_page >= total_canvas_pages,
            ):
                st.session_state.canvas_page += 1
                st.rerun()
        with nav_col3:
            st.markdown(
                f'<div class="section-note">현재 표시 범위: {canvas_start + 1} - {canvas_end} / {total_pages}장</div>',
                unsafe_allow_html=True,
            )
        with nav_col4:
            st.markdown(
                '<div class="section-note">정렬 UX는 드래그 대신 선택 이동을 기본으로 설계했습니다.</div>',
                unsafe_allow_html=True,
            )

        sort_col1, sort_col2 = st.columns(2)
        with sort_col1:
            if st.button("A-Z / 1-9 정렬", use_container_width=True):
                sort_page_items_by_source(reverse=False)
                st.rerun()
        with sort_col2:
            if st.button("Z-A / 9-1 역정렬", use_container_width=True):
                sort_page_items_by_source(reverse=True)
                st.rerun()

        selection_col1, selection_col2, selection_col3, selection_col4 = st.columns(4)
        with selection_col1:
            if st.button("현재 묶음 전체 선택", use_container_width=True):
                select_page_ids([page["id"] for page in visible_pages])
                st.rerun()
        with selection_col2:
            if st.button("전체 선택", use_container_width=True):
                select_page_ids([page["id"] for page in st.session_state.page_items])
                st.rerun()
        with selection_col3:
            if st.button("선택 해제", use_container_width=True, disabled=selected_count == 0):
                clear_selection()
                st.rerun()
        with selection_col4:
            if st.button("선택 페이지 삭제", use_container_width=True, disabled=selected_count == 0):
                remove_pages_by_ids(get_selected_page_ids_in_order())
                st.rerun()

        selected_ids = get_selected_page_ids_in_order()
        remaining_slots = max(1, total_pages - len(selected_ids) + 1)
        st.session_state.move_target_position_state = max(
            1,
            min(st.session_state.move_target_position_state, remaining_slots),
        )
        st.session_state.move_target_position_input = max(
            1,
            min(st.session_state.move_target_position_input, remaining_slots),
        )

        move_col1, move_col2 = st.columns([2, 1])
        with move_col1:
            st.number_input(
                "선택 페이지를 배치할 시작 위치",
                min_value=1,
                max_value=remaining_slots,
                step=1,
                key="move_target_position_input",
                disabled=selected_count == 0,
                help="예: 5를 입력하면 선택한 페이지 묶음이 최종 순서의 5번째 슬롯부터 배치됩니다.",
            )
            st.session_state.move_target_position_state = st.session_state.move_target_position_input
        with move_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("선택 페이지 이동", type="primary", use_container_width=True, disabled=selected_count == 0):
                moved = move_selected_pages(st.session_state.move_target_position_input - 1)
                if moved:
                    st.rerun()

        if st.session_state.insert_position == 0:
            st.markdown(
                '<div class="insert-banner">현재 삽입 위치는 문서 맨 앞입니다.</div>',
                unsafe_allow_html=True,
            )

        cards_per_row = 4
        for row_start in range(0, len(visible_pages), cards_per_row):
            cols = st.columns(cards_per_row)
            for offset, col in enumerate(cols):
                page_offset = row_start + offset
                if page_offset >= len(visible_pages):
                    continue

                page = visible_pages[page_offset]
                global_index = canvas_start + page_offset

                with col:
                    with st.container(border=True):
                        st.markdown(
                            f"""
<div class="page-topline">
    <span class="page-chip">#{global_index + 1}</span>
    <span class="source-pill">{page['source_kind']}</span>
</div>
""",
                            unsafe_allow_html=True,
                        )
                        st.image(page["thumbnail"], use_container_width=True)
                        st.markdown(
                            f'<div class="page-meta">{html.escape(page["source_name"])}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            (
                                f'<div class="page-submeta">원본 {page["source_page_number"]} / '
                                f'{page["source_total_pages"]} 페이지</div>'
                            ),
                            unsafe_allow_html=True,
                        )

                        checkbox_key = f"select_{page['id']}"
                        if checkbox_key not in st.session_state:
                            st.session_state[checkbox_key] = page["id"] in st.session_state.selected_page_ids
                        is_selected = st.checkbox("선택", key=checkbox_key)
                        if is_selected:
                            st.session_state.selected_page_ids.add(page["id"])
                        else:
                            st.session_state.selected_page_ids.discard(page["id"])

                        action_col1, action_col2 = st.columns(2)
                        with action_col1:
                            if st.button(
                                "앞으로",
                                key=f"prev_{page['id']}",
                                use_container_width=True,
                                disabled=global_index == 0,
                            ):
                                move_single_page(page["id"], -1)
                                st.rerun()
                        with action_col2:
                            if st.button(
                                "뒤로",
                                key=f"next_{page['id']}",
                                use_container_width=True,
                                disabled=global_index == total_pages - 1,
                            ):
                                move_single_page(page["id"], 1)
                                st.rerun()

                        if st.button("여기 뒤에 삽입", key=f"insert_{page['id']}", use_container_width=True):
                            set_insert_position(global_index + 1)
                            st.rerun()

                        if st.button("이 페이지 삭제", key=f"delete_{page['id']}", use_container_width=True):
                            remove_pages_by_ids([page["id"]])
                            st.rerun()

                        if st.session_state.insert_position == global_index + 1:
                            st.markdown(
                                '<div class="insert-banner">새 문서는 이 페이지 뒤에 들어갑니다.</div>',
                                unsafe_allow_html=True,
                            )

        if st.session_state.insert_position >= total_pages:
            st.markdown(
                '<div class="insert-banner">현재 삽입 위치는 문서 맨 뒤입니다.</div>',
                unsafe_allow_html=True,
            )

if total_pages:
    st.markdown('<div class="section-kicker">EXPORT</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">편집 결과 저장</div>', unsafe_allow_html=True)

    with st.container(border=True):
        export_col1, export_col2 = st.columns([3, 1])
        with export_col1:
            output_filename = st.text_input(
                "저장할 파일 이름",
                value=st.session_state.export_filename,
                help="현재 페이지 순서와 삭제 상태가 그대로 반영된 새 PDF가 생성됩니다.",
            )
            if not output_filename.endswith(".pdf"):
                output_filename += ".pdf"
            st.session_state.export_filename = output_filename
        with export_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("편집본 만들기", type="primary", use_container_width=True):
                with st.spinner("현재 페이지 캔버스를 새 PDF로 저장하는 중입니다..."):
                    st.session_state.output_pdf_bytes = build_output_pdf()

        if st.session_state.output_pdf_bytes:
            st.success("편집본 PDF가 준비되었습니다. 바로 다운로드할 수 있습니다.")
            st.download_button(
                label="편집본 PDF 다운로드",
                data=st.session_state.output_pdf_bytes,
                file_name=st.session_state.export_filename,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )

st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #6c7a80; padding: 1rem 0 2rem 0;">
    <div style="font-family: 'Fraunces', serif; font-size: 1.1rem; color: #1d2930;">PDF Page Studio</div>
    <div style="font-size: 0.9rem; margin-top: 0.35rem;">페이지 분해, 재배열, 삽입, 삭제를 한 화면에서 처리하는 Streamlit 기반 편집기</div>
</div>
""",
    unsafe_allow_html=True,
)
