import io
import uuid

import fitz
import pytest


def make_pdf_bytes(page_count: int = 1) -> bytes:
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 72), f"Test page {i + 1}")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    buf.seek(0)
    return buf.read()


def make_page_item(
    doc_id: str = None,
    source_name: str = "doc.pdf",
    source_kind: str = "PDF",
    source_page_number: int = 1,
    source_total_pages: int = 1,
) -> dict:
    return {
        "id": uuid.uuid4().hex,
        "document_id": doc_id or uuid.uuid4().hex,
        "source_name": source_name,
        "source_kind": source_kind,
        "source_page_number": source_page_number,
        "source_total_pages": source_total_pages,
        "thumbnail": b"",
    }


@pytest.fixture
def minimal_pdf() -> bytes:
    return make_pdf_bytes(1)


@pytest.fixture
def three_page_pdf() -> bytes:
    return make_pdf_bytes(3)


@pytest.fixture
def simple_page_items():
    doc_id = uuid.uuid4().hex
    return [
        make_page_item(doc_id=doc_id, source_name="a.pdf", source_page_number=i + 1, source_total_pages=3)
        for i in range(3)
    ]
