import io
from typing import Optional

import fitz
from pypdf import PdfReader, PdfWriter


def format_file_size(size_in_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(max(0, size_in_bytes))
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


def get_pymupdf_save_candidates(compression_profile: str) -> list:
    if compression_profile == "maximum":
        return [
            {
                "garbage": 4,
                "clean": True,
                "deflate": True,
                "deflate_images": True,
                "deflate_fonts": True,
                "use_objstms": 1,
            },
            {
                "garbage": 4,
                "clean": True,
                "deflate": True,
                "deflate_images": True,
                "deflate_fonts": True,
            },
            {"garbage": 4, "clean": True, "deflate": True},
            {"garbage": 4, "deflate": True},
            {"garbage": 3, "deflate": True},
        ]

    return [
        {"garbage": 3, "deflate": True, "use_objstms": 1},
        {"garbage": 3, "deflate": True},
        {"garbage": 3},
    ]


def try_lossless_pypdf_optimization(pdf_bytes: bytes) -> Optional[bytes]:
    writer = None
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        for page in writer.pages:
            compress_streams = getattr(page, "compress_content_streams", None)
            if callable(compress_streams):
                try:
                    compress_streams()
                except Exception:
                    continue

        compress_objects = getattr(writer, "compress_identical_objects", None)
        if callable(compress_objects):
            try:
                compress_objects(remove_duplicates=True, remove_unreferenced=True)
            except TypeError:
                compress_objects()

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        return output_stream.getvalue()
    except Exception:
        return None
    finally:
        if writer is not None:
            writer.close()


def try_lossless_pymupdf_optimization(pdf_bytes: bytes, compression_profile: str) -> Optional[bytes]:
    for save_kwargs in get_pymupdf_save_candidates(compression_profile):
        doc = None
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            return doc.tobytes(**save_kwargs)
        except TypeError:
            continue
        except Exception:
            return None
        finally:
            if doc is not None:
                doc.close()
    return None


def optimize_pdf_bytes(pdf_bytes: bytes, compression_profile: str) -> tuple:
    """Returns (optimized_bytes, meta_dict)."""
    warnings = []
    candidates = [{"stage": "assembled", "label": "조립본", "bytes": pdf_bytes}]

    if compression_profile == "none":
        return pdf_bytes, {
            "profile": compression_profile,
            "assembled_size": len(pdf_bytes),
            "final_size": len(pdf_bytes),
            "saved_bytes": 0,
            "saved_percent": 0.0,
            "selected_stage": "assembled",
            "selected_stage_label": "조립본",
            "warnings": warnings,
        }

    pypdf_bytes = try_lossless_pypdf_optimization(pdf_bytes)
    if pypdf_bytes:
        candidates.append({"stage": "pypdf", "label": "객체 정리본", "bytes": pypdf_bytes})
    else:
        warnings.append("pypdf 최적화 단계를 건너뛰고 가능한 압축만 적용했습니다.")

    pymupdf_source = pypdf_bytes or pdf_bytes
    pymupdf_bytes = try_lossless_pymupdf_optimization(pymupdf_source, compression_profile)
    if pymupdf_bytes:
        candidates.append({"stage": "pymupdf", "label": "무손실 압축본", "bytes": pymupdf_bytes})
    else:
        warnings.append("PyMuPDF 저장 최적화 단계를 건너뛰고 가장 작은 결과를 유지했습니다.")

    best = min(candidates, key=lambda c: len(c["bytes"]))
    saved_bytes = max(0, len(pdf_bytes) - len(best["bytes"]))
    saved_percent = (saved_bytes / len(pdf_bytes) * 100) if pdf_bytes else 0.0

    return best["bytes"], {
        "profile": compression_profile,
        "assembled_size": len(pdf_bytes),
        "final_size": len(best["bytes"]),
        "saved_bytes": saved_bytes,
        "saved_percent": saved_percent,
        "selected_stage": best["stage"],
        "selected_stage_label": best["label"],
        "warnings": warnings,
    }


def assemble_pdf(page_items: list, documents: dict) -> bytes:
    """Assembles page_items into a single PDF and returns the raw bytes."""
    writer = PdfWriter()
    reader_cache: dict = {}
    try:
        for page in page_items:
            doc_id = page["document_id"]
            if doc_id not in reader_cache:
                reader_cache[doc_id] = PdfReader(io.BytesIO(documents[doc_id]["pdf_bytes"]))
            reader = reader_cache[doc_id]
            writer.add_page(reader.pages[page["source_page_number"] - 1])

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return output.getvalue()
    finally:
        writer.close()
