import io
from unittest.mock import MagicMock

import pytest
from pypdf import PdfReader

from pdf_studio.canvas import build_document_from_upload
from pdf_studio.conversion import DOCX_TEXT_SUPPORT
from tests.conftest import make_pdf_bytes


def _mock_upload(name: str, content: bytes) -> MagicMock:
    f = MagicMock()
    f.name = name
    f.getvalue.return_value = content
    return f


def _make_png_bytes() -> bytes:
    from PIL import Image
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


class TestBuildDocumentFromUpload:
    def test_pdf_upload_returns_document_and_pages(self):
        pdf_bytes = make_pdf_bytes(2)
        f = _mock_upload("test.pdf", pdf_bytes)
        doc, pages, notices = build_document_from_upload(f)
        assert doc["kind"] == "PDF"
        assert doc["page_count"] == 2
        assert len(pages) == 2
        assert notices == []

    def test_document_has_required_keys(self):
        f = _mock_upload("test.pdf", make_pdf_bytes(1))
        doc, _, _ = build_document_from_upload(f)
        for key in ("id", "name", "kind", "pdf_bytes", "page_count"):
            assert key in doc

    def test_pdf_bytes_stored_in_document(self):
        pdf_bytes = make_pdf_bytes(1)
        f = _mock_upload("test.pdf", pdf_bytes)
        doc, _, _ = build_document_from_upload(f)
        reader = PdfReader(io.BytesIO(doc["pdf_bytes"]))
        assert len(reader.pages) == 1

    def test_png_upload_converts_to_pdf(self):
        f = _mock_upload("image.png", _make_png_bytes())
        doc, pages, _ = build_document_from_upload(f)
        assert doc["kind"] == "IMAGE"
        assert doc["page_count"] == 1
        assert len(pages) == 1

    def test_jpg_extension_accepted(self):
        f = _mock_upload("photo.jpg", _make_png_bytes())
        doc, _, _ = build_document_from_upload(f)
        assert doc["kind"] == "IMAGE"

    def test_unsupported_extension_raises(self):
        f = _mock_upload("file.txt", b"hello")
        with pytest.raises(ValueError, match="지원하지 않는"):
            build_document_from_upload(f)

    def test_page_items_contain_thumbnails(self):
        f = _mock_upload("test.pdf", make_pdf_bytes(1))
        _, pages, _ = build_document_from_upload(f)
        assert isinstance(pages[0]["thumbnail"], bytes)
        assert len(pages[0]["thumbnail"]) > 0

    def test_all_pages_share_document_id(self):
        f = _mock_upload("test.pdf", make_pdf_bytes(3))
        doc, pages, _ = build_document_from_upload(f)
        assert all(p["document_id"] == doc["id"] for p in pages)

    def test_source_name_is_filename(self):
        f = _mock_upload("my_report.pdf", make_pdf_bytes(1))
        _, pages, _ = build_document_from_upload(f)
        assert pages[0]["source_name"] == "my_report.pdf"

    @pytest.mark.skipif(not DOCX_TEXT_SUPPORT, reason="python-docx or reportlab not available")
    def test_docx_upload_converts(self):
        from docx import Document as DocxDocument
        doc = DocxDocument()
        doc.add_paragraph("Hello")
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        f = _mock_upload("report.docx", buf.read())
        result_doc, pages, _ = build_document_from_upload(f)
        assert result_doc["kind"] == "DOCX"
        assert result_doc["page_count"] >= 1
