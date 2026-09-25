"""Plain-text extraction for uploaded PDF/TXT knowledge sources."""

import io

from pypdf import PdfReader


class ExtractionError(Exception):
    pass


def extract_pdf_text(raw_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise ExtractionError(f"Could not read PDF: {exc}") from exc

    text = "\n\n".join(p for p in pages if p.strip())
    if not text.strip():
        raise ExtractionError("PDF contains no extractable text (likely a scanned image)")
    return text


def extract_txt_text(raw_bytes: bytes) -> str:
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ExtractionError(f"File is not valid UTF-8 text: {exc}") from exc

    if not text.strip():
        raise ExtractionError("Text file is empty")
    return text
