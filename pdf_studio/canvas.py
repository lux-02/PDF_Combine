import os
import uuid

import fitz

from pdf_studio.conversion import DOCX_TEXT_SUPPORT, docx_to_pdf_simple, image_to_pdf_bytes

THUMBNAIL_SCALE = 0.30
SUPPORTED_TYPES = ["pdf", "jpg", "jpeg", "png", "docx"]


def create_page_items(
    pdf_bytes: bytes,
    document_id: str,
    source_name: str,
    source_kind: str,
) -> list:
    """Renders each page as a thumbnail and returns a list of page item dicts."""
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


def build_document_from_upload(uploaded_file) -> tuple:
    """Returns (document_dict, page_items, notices)."""
    raw_bytes = uploaded_file.getvalue()
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    document_id = uuid.uuid4().hex
    notices = []

    if file_ext == ".pdf":
        pdf_bytes = raw_bytes
        source_kind = "PDF"
    elif file_ext == ".docx":
        if not DOCX_TEXT_SUPPORT:
            raise RuntimeError(
                "DOCX 변환에 필요한 python-docx 또는 reportlab이 설치되어 있지 않습니다."
            )
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
    elif file_ext in (".jpg", ".jpeg", ".png"):
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
