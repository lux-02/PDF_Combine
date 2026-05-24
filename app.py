import io
import re
from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from pypdf import PdfReader, PdfWriter

from pdf_studio.export import optimize_pdf_bytes

PUBLIC_DIR = Path(__file__).parent / "public"
DEFAULT_FILENAME = "combined.pdf"
MAX_FILES = 50

app = FastAPI(title="PDF Combiner", docs_url="/api/docs", redoc_url=None)


def normalize_pdf_filename(filename: str | None) -> str:
    base = (filename or DEFAULT_FILENAME).strip()
    base = re.sub(r'[\\/:*?"<>|]+', "-", base)
    base = re.sub(r"\s+", " ", base).strip(" .")
    if not base:
        base = DEFAULT_FILENAME
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    return base


def content_disposition(filename: str) -> str:
    encoded = quote(filename)
    return f"attachment; filename*=UTF-8''{encoded}"


async def read_pdf_upload(upload: UploadFile) -> bytes:
    if not upload.filename or not upload.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail=f"{upload.filename or 'file'}: PDF만 업로드할 수 있습니다.")

    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail=f"{upload.filename}: 빈 파일입니다.")
    return data


async def combine_uploads(files: list[UploadFile]) -> bytes:
    if not files:
        raise HTTPException(status_code=400, detail="합칠 PDF를 선택하세요.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"한 번에 최대 {MAX_FILES}개까지 합칠 수 있습니다.")

    writer = PdfWriter()
    try:
        for upload in files:
            data = await read_pdf_upload(upload)
            try:
                reader = PdfReader(io.BytesIO(data))
                if reader.is_encrypted:
                    try:
                        reader.decrypt("")
                    except Exception as exc:
                        raise ValueError("암호화된 PDF는 처리할 수 없습니다.") from exc
                for page in reader.pages:
                    writer.add_page(page)
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"{upload.filename}: PDF를 읽을 수 없습니다.",
                ) from exc

        output = io.BytesIO()
        writer.write(output)
        return optimize_pdf_bytes(output.getvalue(), "balanced")[0]
    finally:
        writer.close()


@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/index.html", status_code=307)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/{asset_name}", include_in_schema=False)
def public_asset(asset_name: str):
    asset_path = PUBLIC_DIR / asset_name
    if not asset_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(asset_path)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/combine")
async def combine_pdf(
    files: Annotated[list[UploadFile], File(description="Ordered PDF files")],
    filename: Annotated[str, Form()] = DEFAULT_FILENAME,
):
    combined_pdf = await combine_uploads(files)
    output_filename = normalize_pdf_filename(filename)
    return Response(
        content=combined_pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": content_disposition(output_filename)},
    )


@app.post("/api/optimize")
async def optimize_pdf(
    file: Annotated[UploadFile, File(description="PDF to optimize")],
    filename: Annotated[str, Form()] = "",
):
    data = await read_pdf_upload(file)
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:
                raise HTTPException(status_code=400, detail="암호화된 PDF는 처리할 수 없습니다.") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{file.filename}: PDF를 읽을 수 없습니다.",
        ) from exc

    optimized, meta = optimize_pdf_bytes(data, "balanced")
    output_filename = normalize_pdf_filename(filename or file.filename or DEFAULT_FILENAME)

    return Response(
        content=optimized,
        media_type="application/pdf",
        headers={
            "Content-Disposition": content_disposition(output_filename),
            "X-Original-Size": str(meta["assembled_size"]),
            "X-Optimized-Size": str(meta["final_size"]),
            "X-Saved-Percent": f"{meta['saved_percent']:.1f}",
        },
    )
