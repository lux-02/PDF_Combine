import io

import pytest
from pypdf import PdfReader

from pdf_studio.canvas import create_page_items


class TestCreatePageItems:
    def test_creates_correct_count(self, three_page_pdf):
        items = create_page_items(three_page_pdf, "doc1", "test.pdf", "PDF")
        assert len(items) == 3

    def test_each_item_has_required_keys(self, minimal_pdf):
        items = create_page_items(minimal_pdf, "doc1", "test.pdf", "PDF")
        required = {"id", "document_id", "source_name", "source_kind",
                    "source_page_number", "source_total_pages", "thumbnail"}
        for item in items:
            assert required.issubset(item.keys())

    def test_source_page_numbers_are_sequential(self, three_page_pdf):
        items = create_page_items(three_page_pdf, "doc1", "test.pdf", "PDF")
        assert [i["source_page_number"] for i in items] == [1, 2, 3]

    def test_source_total_pages_is_correct(self, three_page_pdf):
        items = create_page_items(three_page_pdf, "doc1", "test.pdf", "PDF")
        for item in items:
            assert item["source_total_pages"] == 3

    def test_document_id_propagated(self, minimal_pdf):
        items = create_page_items(minimal_pdf, "my_doc_id", "test.pdf", "PDF")
        assert all(i["document_id"] == "my_doc_id" for i in items)

    def test_source_name_propagated(self, minimal_pdf):
        items = create_page_items(minimal_pdf, "doc1", "my_file.pdf", "PDF")
        assert all(i["source_name"] == "my_file.pdf" for i in items)

    def test_each_item_has_unique_id(self, three_page_pdf):
        items = create_page_items(three_page_pdf, "doc1", "test.pdf", "PDF")
        ids = [i["id"] for i in items]
        assert len(ids) == len(set(ids))

    def test_thumbnail_is_bytes(self, minimal_pdf):
        items = create_page_items(minimal_pdf, "doc1", "test.pdf", "PDF")
        assert isinstance(items[0]["thumbnail"], bytes)
        assert len(items[0]["thumbnail"]) > 0

    def test_empty_pdf_raises(self):
        from pypdf import PdfWriter
        writer = PdfWriter()
        buf = io.BytesIO()
        writer.write(buf)
        writer.close()
        with pytest.raises(ValueError, match="페이지"):
            create_page_items(buf.getvalue(), "doc1", "empty.pdf", "PDF")
