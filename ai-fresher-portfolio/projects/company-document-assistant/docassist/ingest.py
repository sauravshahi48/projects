import hashlib
import re
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import PurePosixPath

from pypdf import PdfReader

from .config import Settings
from .models import Chunk, Document, Page


class DocumentError(ValueError):
    pass


def safe_filename(name: str) -> str:
    # Windows and Unix path components are both stripped. Never use this name on disk.
    name = PurePosixPath(name.replace("\\", "/")).name
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()[:160]
    if not name:
        raise DocumentError("Please provide a filename.")
    return name


def extract_document(name: str, data: bytes, settings: Settings) -> Document:
    name = safe_filename(name)
    if not data:
        raise DocumentError("The file is empty.")
    if len(data) > settings.max_bytes:
        raise DocumentError("The file exceeds the 10 MB upload limit.")
    extension = PurePosixPath(name).suffix.lower()
    if extension == ".pdf":
        mime_type = "application/pdf"
        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                raise DocumentError(
                    "Password-protected PDFs are not supported. Upload a readable copy."
                )
            if len(reader.pages) > settings.max_pages:
                raise DocumentError(f"PDFs may contain at most {settings.max_pages} pages.")
            pages = []
            characters = 0
            for number, pdf_page in enumerate(reader.pages, 1):
                # Refuse unusually large uncompressed streams before text extraction.
                stream = pdf_page.get_contents()
                if stream is not None and len(stream.get_data()) > 8_000_000:
                    raise DocumentError("A PDF page is too complex. Upload a simpler PDF.")
                text = (pdf_page.extract_text() or "").replace("\x00", " ").strip()
                characters += len(text)
                if characters > settings.max_characters:
                    raise DocumentError("The extracted document is too large for this demo.")
                pages.append(Page(number=number, text=text))
        except DocumentError:
            raise
        except Exception as exc:
            raise DocumentError(
                "This PDF could not be read. Check that it is a valid PDF."
            ) from exc
    elif extension in {".txt", ".md"}:
        mime_type = "text/plain; charset=utf-8"
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentError("Text files must use UTF-8 encoding.") from exc
        pages = [Page(i, t.replace("\x00", " ").strip()) for i, t in enumerate(text.split("\f"), 1)]
        if len(pages) > settings.max_pages or len(text) > settings.max_characters:
            raise DocumentError("The text document is too large for this demo.")
    else:
        raise DocumentError("Supported file types: PDF, TXT and Markdown.")
    if not any(len(p.text.strip()) >= 15 for p in pages):
        raise DocumentError("No readable text found. Image-only scans need OCR before upload.")
    return Document(
        id=uuid.uuid4().hex,
        name=name,
        sha256=hashlib.sha256(data).hexdigest(),
        mime_type=mime_type,
        created_at=datetime.now(timezone.utc).isoformat(),
        pages=tuple(pages),
        data=data,
    )


def chunk_document(document: Document, settings: Settings) -> list[Chunk]:
    """Overlapping chunks never cross a page, preserving trustworthy page references."""
    chunks = []
    for page in document.pages:
        text = re.sub(r"\s+", " ", page.text).strip()
        start = 0
        part = 0
        while start < len(text):
            end = min(start + settings.chunk_size, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start + settings.chunk_size // 2, end)
                if boundary > start:
                    end = boundary
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(
                    Chunk(
                        id=f"{document.id}:{page.number}:{part}",
                        document_id=document.id,
                        filename=document.name,
                        page=page.number,
                        text=chunk,
                    )
                )
            if end >= len(text):
                break
            start = max(start + 1, end - settings.chunk_overlap)
            part += 1
    return chunks
