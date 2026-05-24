import io

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app import app, normalize_pdf_filename


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_normalize_pdf_filename():
    assert normalize_pdf_filename("combined") == "combined.pdf"
    assert normalize_pdf_filename("bad/name?.pdf") == "bad-name-.pdf"
    assert normalize_pdf_filename("   ") == "combined.pdf"


def test_combine_endpoint_preserves_upload_order(minimal_pdf, three_page_pdf):
    response = client.post(
        "/api/combine",
        data={"filename": "result.pdf"},
        files=[
            ("files", ("one.pdf", minimal_pdf, "application/pdf")),
            ("files", ("three.pdf", three_page_pdf, "application/pdf")),
        ],
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "result.pdf" in response.headers["content-disposition"]

    reader = PdfReader(io.BytesIO(response.content))
    assert len(reader.pages) == 4


def test_combine_endpoint_rejects_non_pdf(minimal_pdf):
    response = client.post(
        "/api/combine",
        files=[("files", ("not-pdf.txt", minimal_pdf, "text/plain"))],
    )

    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_optimize_endpoint_returns_compressed_pdf(minimal_pdf):
    response = client.post(
        "/api/optimize",
        data={"filename": "output.pdf"},
        files=[("file", ("input.pdf", minimal_pdf, "application/pdf"))],
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "output.pdf" in response.headers["content-disposition"]
    assert int(response.headers["x-original-size"]) > 0
    assert int(response.headers["x-optimized-size"]) > 0
    assert float(response.headers["x-saved-percent"]) >= 0
    reader = PdfReader(io.BytesIO(response.content))
    assert len(reader.pages) >= 1


def test_optimize_endpoint_rejects_non_pdf(minimal_pdf):
    response = client.post(
        "/api/optimize",
        files=[("file", ("not-pdf.txt", minimal_pdf, "text/plain"))],
    )

    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_optimize_endpoint_rejects_empty_file():
    response = client.post(
        "/api/optimize",
        files=[("file", ("empty.pdf", b"", "application/pdf"))],
    )

    assert response.status_code == 400
