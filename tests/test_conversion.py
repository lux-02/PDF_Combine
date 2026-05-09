import io

import pytest
from PIL import Image
from pypdf import PdfReader

from pdf_studio.conversion import find_korean_font_path, image_to_pdf_bytes


# ---------------------------------------------------------------------------
# find_korean_font_path
# ---------------------------------------------------------------------------

class TestFindKoreanFontPath:
    def test_returns_string_or_none(self):
        result = find_korean_font_path()
        assert result is None or isinstance(result, str)

    def test_path_exists_when_found(self):
        import os
        result = find_korean_font_path()
        if result is not None:
            assert os.path.exists(result)

    def test_path_ends_with_ttf(self):
        result = find_korean_font_path()
        if result is not None:
            assert result.lower().endswith(".ttf")


# ---------------------------------------------------------------------------
# image_to_pdf_bytes
# ---------------------------------------------------------------------------

class TestImageToPdfBytes:
    def _make_rgb_image_bytes(self, width: int = 100, height: int = 100) -> bytes:
        img = Image.new("RGB", (width, height), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()

    def _make_rgba_image_bytes(self) -> bytes:
        img = Image.new("RGBA", (100, 100), color=(0, 255, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()

    def _make_palette_image_bytes(self) -> bytes:
        img = Image.new("P", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()

    def test_rgb_image_converts_to_pdf(self):
        result = image_to_pdf_bytes(self._make_rgb_image_bytes())
        assert isinstance(result, bytes)
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_rgba_image_converts_without_error(self):
        result = image_to_pdf_bytes(self._make_rgba_image_bytes())
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_palette_image_converts_without_error(self):
        result = image_to_pdf_bytes(self._make_palette_image_bytes())
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_large_image(self):
        result = image_to_pdf_bytes(self._make_rgb_image_bytes(2000, 3000))
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_returns_bytes_type(self):
        result = image_to_pdf_bytes(self._make_rgb_image_bytes())
        assert isinstance(result, bytes)
