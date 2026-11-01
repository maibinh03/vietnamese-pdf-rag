from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


class InvalidDocument(ValueError):
    pass


@dataclass(frozen=True)
class TextPage:
    page: int | None
    text: str


@dataclass(frozen=True)
class TextChunk:
    page: int | None
    chunk_index: int
    char_start: int
    char_end: int
    text: str


def extract_pages(filename: str, content: bytes) -> list[TextPage]:
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix == "txt":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InvalidDocument("TXT phải được mã hóa UTF-8.") from exc
        if not text.strip():
            raise InvalidDocument("Tài liệu không có văn bản.")
        return [TextPage(page=None, text=text)]
    if suffix != "pdf":
        raise InvalidDocument("Chỉ chấp nhận tệp PDF hoặc TXT.")
    if not content.startswith(b"%PDF-"):
        raise InvalidDocument("Nội dung tệp không có định dạng PDF hợp lệ.")
    try:
        reader = PdfReader(BytesIO(content), strict=True)
        pages = [
            TextPage(page=index, text=page.extract_text() or "")
            for index, page in enumerate(reader.pages, start=1)
        ]
    except Exception as exc:
        raise InvalidDocument("Không thể đọc tệp PDF.") from exc
    pages = [page for page in pages if page.text.strip()]
    if not pages:
        raise InvalidDocument("PDF không chứa văn bản có thể trích xuất.")
    return pages


def chunk_pages(
    pages: list[TextPage], chunk_size: int, overlap: int
) -> list[TextChunk]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size phải dương và overlap phải nhỏ hơn chunk_size.")
    chunks: list[TextChunk] = []
    chunk_index = 0
    for page in pages:
        text = page.text
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start + chunk_size // 2, end)
                if boundary > start:
                    end = boundary
            chunk_text = text[start:end]
            if chunk_text.strip():
                chunks.append(
                    TextChunk(
                        page=page.page,
                        chunk_index=chunk_index,
                        char_start=start,
                        char_end=end,
                        text=chunk_text,
                    )
                )
                chunk_index += 1
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks
