import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from pdf_rag.config import Settings
from pdf_rag.ingestion import InvalidDocument, extract_pages
from pdf_rag.main import create_app
from pdf_rag.repository import DocumentRepository
from pdf_rag.service import ABSTENTION, RagService


def make_text_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)


class FakeEmbedder:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 384 for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 384


class FakeVectorStore:
    def __init__(self) -> None:
        self.items: list[dict] = []
        self.raise_on_search = False

    def ensure_collection(self) -> None:
        pass

    def upsert(self, vectors: list[list[float]], payloads: list[dict]) -> list[str]:
        self.items.extend(payloads)
        return [str(index) for index in range(len(payloads))]

    def delete(self, point_ids: list[str]) -> None:
        pass

    def search(self, vector: list[float], limit: int) -> list[dict]:
        if self.raise_on_search:
            raise ConnectionError("qdrant offline")
        if not self.items:
            return []
        return [{**self.items[0], "score": 0.9}]

    def health(self) -> None:
        if self.raise_on_search:
            raise ConnectionError("qdrant offline")


class FakeLLM:
    def __init__(self) -> None:
        self.raise_on_answer = False
        self.called = False

    def answer(self, question: str, evidence: list[dict]) -> str:
        self.called = True
        if self.raise_on_answer:
            raise ConnectionError("ollama offline")
        return "Chuyển khoản nội bộ miễn phí [S1]."

    def health(self) -> None:
        if self.raise_on_answer:
            raise ConnectionError("ollama offline")


class DocumentRagApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = Settings(
            database_path=str(Path(self.temp_dir.name) / "metadata.db"),
            chunk_size=200,
            chunk_overlap=20,
            max_upload_size_bytes=2048,
            min_relevance_score=0.35,
        )
        self.store = FakeVectorStore()
        self.llm = FakeLLM()
        self.service = RagService(
            self.settings,
            repository=DocumentRepository(self.settings.database_path),
            embedder=FakeEmbedder(),
            vector_store=self.store,
            llm=self.llm,
        )
        self.client = TestClient(create_app(self.service))
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def test_valid_pdf_is_extracted_and_indexed(self) -> None:
        text = "Solar energy converts sunlight into electricity."
        content = make_text_pdf(text)
        self.assertEqual(self.client.app.title, "PDF Document Q&A")
        self.assertEqual(extract_pages("guide.pdf", content)[0].text.strip(), text)
        response = self.client.post(
            "/documents", files={"file": ("guide.pdf", content, "application/pdf")}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["chunk_count"], 1)
        self.assertEqual(self.store.items[0]["page"], 1)
        self.assertEqual(self.store.items[0]["text"].strip(), text)

    def test_unreadable_pdf_is_rejected(self) -> None:
        response = self.client.post(
            "/documents",
            files={"file": ("broken.pdf", b"%PDF-not-readable", "application/pdf")},
        )
        self.assertEqual(response.status_code, 422)

    def test_duplicate_document_is_rejected(self) -> None:
        content = b"Phi tai khoan bang khong."
        first = self.client.post(
            "/documents", files={"file": ("fees.txt", content, "text/plain")}
        )
        second = self.client.post(
            "/documents", files={"file": ("fees.txt", content, "text/plain")}
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(len(self.client.get("/documents").json()["documents"]), 1)

    def test_clear_vietnamese_question_returns_citation(self) -> None:
        uploaded = self.client.post(
            "/documents",
            files={"file": ("digital.txt", "Chuyển khoản nội bộ miễn phí.".encode(), "text/plain")},
        )
        self.assertEqual(uploaded.status_code, 201)
        response = self.client.post(
            "/chat", json={"question": "Chuyển khoản nội bộ có mất phí không?"}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["abstained"])
        self.assertEqual(body["citations"][0]["filename"], "digital.txt")
        self.assertGreaterEqual(body["retrieval_latency_ms"], 0)

    def test_no_evidence_abstains_without_calling_llm(self) -> None:
        response = self.client.post("/chat", json={"question": "Ngoài phạm vi?"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["abstained"])
        self.assertEqual(response.json()["answer"], ABSTENTION)
        self.assertFalse(self.llm.called)

    def test_health_reports_degraded_when_llm_is_unavailable(self) -> None:
        self.llm.raise_on_answer = True
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["vector_store"], "ok")
        self.assertEqual(response.json()["llm"], "unavailable")
        self.assertEqual(response.json()["status"], "degraded")

    def test_vector_database_unavailable_returns_503(self) -> None:
        self.store.raise_on_search = True
        response = self.client.post("/chat", json={"question": "Câu hỏi"})
        self.assertEqual(response.status_code, 503)

    def test_llm_unavailable_returns_503(self) -> None:
        self.client.post(
            "/documents",
            files={"file": ("guide.txt", b"Huong dan chuyen tien.", "text/plain")},
        )
        self.llm.raise_on_answer = True
        response = self.client.post("/chat", json={"question": "Câu hỏi"})
        self.assertEqual(response.status_code, 503)

    def test_invalid_request_and_upload_limits_are_rejected(self) -> None:
        bad_format = self.client.post(
            "/documents", files={"file": ("guide.doc", b"text", "text/plain")}
        )
        too_large = self.client.post(
            "/documents",
            files={"file": ("large.txt", b"x" * 2049, "text/plain")},
        )
        malformed_chat = self.client.post("/chat", json={"question": ""})
        self.assertEqual(bad_format.status_code, 415)
        self.assertEqual(too_large.status_code, 413)
        self.assertEqual(malformed_chat.status_code, 422)

    def test_invalid_utf8_text_is_rejected(self) -> None:
        with self.assertRaises(InvalidDocument):
            extract_pages("bad.txt", b"\xff\xfe")


if __name__ == "__main__":
    unittest.main()
