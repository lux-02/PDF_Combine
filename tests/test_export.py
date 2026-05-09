import io
import uuid

import pytest
from pypdf import PdfReader

from pdf_studio.export import (
    assemble_pdf,
    format_file_size,
    get_pymupdf_save_candidates,
    optimize_pdf_bytes,
    try_lossless_pymupdf_optimization,
    try_lossless_pypdf_optimization,
)
from tests.conftest import make_page_item


# ---------------------------------------------------------------------------
# format_file_size
# ---------------------------------------------------------------------------

class TestFormatFileSize:
    def test_bytes(self):
        assert format_file_size(512) == "512 B"

    def test_kilobytes(self):
        assert format_file_size(1024) == "1.0 KB"

    def test_megabytes(self):
        assert format_file_size(1024 * 1024) == "1.0 MB"

    def test_zero(self):
        assert format_file_size(0) == "0 B"

    def test_negative_treated_as_zero(self):
        assert format_file_size(-100) == "0 B"

    def test_gigabytes(self):
        result = format_file_size(1024 ** 3)
        assert "GB" in result


# ---------------------------------------------------------------------------
# get_pymupdf_save_candidates
# ---------------------------------------------------------------------------

class TestGetPymupdfSaveCandidates:
    def test_maximum_returns_multiple_candidates(self):
        candidates = get_pymupdf_save_candidates("maximum")
        assert len(candidates) >= 3

    def test_balanced_returns_candidates(self):
        candidates = get_pymupdf_save_candidates("balanced")
        assert len(candidates) >= 1

    def test_maximum_includes_deflate(self):
        for c in get_pymupdf_save_candidates("maximum"):
            assert c.get("deflate") is True

    def test_all_candidates_are_dicts(self):
        for profile in ("maximum", "balanced"):
            for c in get_pymupdf_save_candidates(profile):
                assert isinstance(c, dict)


# ---------------------------------------------------------------------------
# try_lossless_pypdf_optimization
# ---------------------------------------------------------------------------

class TestTryLosslessPypdfOptimization:
    def test_returns_bytes_for_valid_pdf(self, minimal_pdf):
        result = try_lossless_pypdf_optimization(minimal_pdf)
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_result_is_valid_pdf(self, minimal_pdf):
        result = try_lossless_pypdf_optimization(minimal_pdf)
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_returns_none_for_garbage(self):
        result = try_lossless_pypdf_optimization(b"not a pdf at all")
        assert result is None


# ---------------------------------------------------------------------------
# try_lossless_pymupdf_optimization
# ---------------------------------------------------------------------------

class TestTryLosslessPymupdfOptimization:
    def test_returns_bytes_for_valid_pdf(self, minimal_pdf):
        result = try_lossless_pymupdf_optimization(minimal_pdf, "balanced")
        assert result is not None
        assert isinstance(result, bytes)

    def test_maximum_profile(self, minimal_pdf):
        result = try_lossless_pymupdf_optimization(minimal_pdf, "maximum")
        assert result is not None

    def test_result_is_valid_pdf(self, minimal_pdf):
        result = try_lossless_pymupdf_optimization(minimal_pdf, "balanced")
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_returns_none_for_garbage(self):
        result = try_lossless_pymupdf_optimization(b"garbage", "balanced")
        assert result is None


# ---------------------------------------------------------------------------
# optimize_pdf_bytes
# ---------------------------------------------------------------------------

class TestOptimizePdfBytes:
    def test_none_profile_returns_original(self, minimal_pdf):
        result, meta = optimize_pdf_bytes(minimal_pdf, "none")
        assert result == minimal_pdf
        assert meta["profile"] == "none"
        assert meta["saved_bytes"] == 0

    def test_balanced_returns_valid_pdf(self, minimal_pdf):
        result, meta = optimize_pdf_bytes(minimal_pdf, "balanced")
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1
        assert meta["profile"] == "balanced"

    def test_maximum_returns_valid_pdf(self, minimal_pdf):
        result, meta = optimize_pdf_bytes(minimal_pdf, "maximum")
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_meta_contains_required_keys(self, minimal_pdf):
        _, meta = optimize_pdf_bytes(minimal_pdf, "balanced")
        for key in ("profile", "assembled_size", "final_size", "saved_bytes", "saved_percent", "warnings"):
            assert key in meta

    def test_final_size_not_larger_than_assembled(self, three_page_pdf):
        _, meta = optimize_pdf_bytes(three_page_pdf, "maximum")
        assert meta["final_size"] <= meta["assembled_size"]

    def test_assembled_size_matches_input(self, minimal_pdf):
        _, meta = optimize_pdf_bytes(minimal_pdf, "balanced")
        assert meta["assembled_size"] == len(minimal_pdf)


# ---------------------------------------------------------------------------
# assemble_pdf
# ---------------------------------------------------------------------------

class TestAssemblePdf:
    def _make_documents_and_items(self, pdf_bytes: bytes):
        doc_id = uuid.uuid4().hex
        documents = {
            doc_id: {"id": doc_id, "name": "test.pdf", "kind": "PDF", "pdf_bytes": pdf_bytes}
        }
        items = [
            make_page_item(doc_id=doc_id, source_page_number=i + 1, source_total_pages=3)
            for i in range(3)
        ]
        return documents, items

    def test_assembles_all_pages(self, three_page_pdf):
        documents, items = self._make_documents_and_items(three_page_pdf)
        result = assemble_pdf(items, documents)
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 3

    def test_assembles_subset(self, three_page_pdf):
        documents, items = self._make_documents_and_items(three_page_pdf)
        result = assemble_pdf(items[:2], documents)
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 2

    def test_returns_bytes(self, three_page_pdf):
        documents, items = self._make_documents_and_items(three_page_pdf)
        result = assemble_pdf(items, documents)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_empty_items_returns_valid_pdf(self, three_page_pdf):
        doc_id = uuid.uuid4().hex
        documents = {
            doc_id: {"id": doc_id, "name": "test.pdf", "kind": "PDF", "pdf_bytes": three_page_pdf}
        }
        result = assemble_pdf([], documents)
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 0

    def test_cross_document_assembly(self, minimal_pdf, three_page_pdf):
        doc1 = uuid.uuid4().hex
        doc2 = uuid.uuid4().hex
        documents = {
            doc1: {"id": doc1, "name": "a.pdf", "kind": "PDF", "pdf_bytes": minimal_pdf},
            doc2: {"id": doc2, "name": "b.pdf", "kind": "PDF", "pdf_bytes": three_page_pdf},
        }
        items = [
            make_page_item(doc_id=doc1, source_page_number=1, source_total_pages=1),
            make_page_item(doc_id=doc2, source_page_number=2, source_total_pages=3),
        ]
        result = assemble_pdf(items, documents)
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 2
