import hashlib
import logging
import re
import time
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from pdf_rag.config import Settings
from pdf_rag.embeddings import Embedder, SentenceTransformerEmbedder
from pdf_rag.ingestion import chunk_pages, extract_pages
from pdf_rag.llm import AnswerGenerator, OllamaClient
from pdf_rag.repository import DocumentRepository
from pdf_rag.schemas import ChatResponse, Citation, DocumentResponse
from pdf_rag.vector_store import QdrantStore, VectorStore

logger = logging.getLogger(__name__)
ABSTENTION = "Tôi không tìm thấy đủ thông tin trong tài liệu để trả lời câu hỏi này."


class DependencyUnavailable(RuntimeError):
    pass


class DuplicateDocument(RuntimeError):
    pass


class RagService:
    def __init__(
        self,
        settings: Settings,
        repository: DocumentRepository | None = None,
        embedder: Embedder | None = None,
        vector_store: VectorStore | None = None,
        llm: AnswerGenerator | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository or DocumentRepository(settings.database_path)
        self.embedder = embedder or SentenceTransformerEmbedder(settings.embedding_model)
        self.vector_store = vector_store or QdrantStore(
            settings.qdrant_url, settings.collection_name
        )
        self.llm = llm or OllamaClient(settings.ollama_url, settings.ollama_model)
        self._collection_ready = False
        self._collection_lock = Lock()

    def initialize(self) -> None:
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if self._collection_ready:
            return
        with self._collection_lock:
            if self._collection_ready:
                return
            try:
                self.vector_store.ensure_collection()
                self._collection_ready = True
            except Exception as exc:
                logger.exception("Qdrant collection initialization failed")
                raise DependencyUnavailable("Vector database không khả dụng.") from exc

    def ingest(self, filename: str, content: bytes) -> DocumentResponse:
        ingest_started = time.perf_counter()
        digest = hashlib.sha256(content).hexdigest()
        if self.repository.find_by_hash(digest):
            raise DuplicateDocument("Tài liệu này đã được nạp.")
        extraction_started = time.perf_counter()
        pages = extract_pages(filename, content)
        chunks = chunk_pages(
            pages, self.settings.chunk_size, self.settings.chunk_overlap
        )
        logger.info(
            "document_extracted filename=%s pages=%d chunks=%d latency_ms=%.2f",
            filename,
            len(pages),
            len(chunks),
            (time.perf_counter() - extraction_started) * 1000,
        )
        try:
            self._ensure_collection()
            embedding_started = time.perf_counter()
            vectors = self.embedder.embed_documents([chunk.text for chunk in chunks])
            logger.info(
                "document_embedded filename=%s chunks=%d latency_ms=%.2f",
                filename,
                len(chunks),
                (time.perf_counter() - embedding_started) * 1000,
            )
            document_id = str(uuid4())
            payloads = [
                {
                    "document_id": document_id,
                    "filename": filename,
                    "sha256": digest,
                    "page": chunk.page,
                    "chunk_index": chunk.chunk_index,
                    "char_start": chunk.char_start,
                    "char_end": chunk.char_end,
                    "text": chunk.text,
                }
                for chunk in chunks
            ]
            indexing_started = time.perf_counter()
            point_ids = self.vector_store.upsert(vectors, payloads)
            logger.info(
                "document_indexed filename=%s points=%d latency_ms=%.2f",
                filename,
                len(point_ids),
                (time.perf_counter() - indexing_started) * 1000,
            )
        except Exception as exc:
            logger.exception("Document indexing failed")
            raise DependencyUnavailable("Không thể lập chỉ mục tài liệu.") from exc
        created_at = datetime.now(UTC).isoformat()
        try:
            document = self.repository.add(
                document_id, filename, digest, len(chunks), created_at
            )
        except Exception:
            try:
                self.vector_store.delete(point_ids)
            except Exception:
                logger.exception("Failed to clean up vectors after metadata write failure")
            raise
        if document is None:
            self.vector_store.delete(point_ids)
            raise DuplicateDocument("Tài liệu này đã được nạp.")
        logger.info(
            "document_ingest_complete filename=%s latency_ms=%.2f",
            filename,
            (time.perf_counter() - ingest_started) * 1000,
        )
        return document

    def list_documents(self) -> list[DocumentResponse]:
        return self.repository.list_documents()

    def chat(self, question: str, top_k: int) -> ChatResponse:
        started = time.perf_counter()
        try:
            self._ensure_collection()
            query_vector = self.embedder.embed_query(question)
            matches = self.vector_store.search(query_vector, top_k)
        except Exception as exc:
            logger.exception("Retrieval failed")
            raise DependencyUnavailable("Retrieval không khả dụng.") from exc
        retrieval_ms = (time.perf_counter() - started) * 1000
        evidence = [
            match
            for match in matches
            if match.get("score", 0) >= self.settings.min_relevance_score
        ]
        if not evidence:
            return ChatResponse(
                answer=ABSTENTION,
                abstained=True,
                citations=[],
                retrieval_latency_ms=round(retrieval_ms, 2),
                generation_latency_ms=0,
            )
        generation_started = time.perf_counter()
        try:
            answer = self.llm.answer(question, evidence)

            logger.info("Raw LLM answer: %r", answer)
            logger.info("Evidence count: %d", len(evidence))
        except Exception as exc:
            logger.exception("Answer generation failed")
            raise DependencyUnavailable("LLM không khả dụng.") from exc
        generation_ms = (time.perf_counter() - generation_started) * 1000
        valid_refs = {f"S{index}" for index in range(1, len(evidence) + 1)}
        cited_refs = set(re.findall(r"\[(S\d+)\]", answer))
        if not cited_refs.issubset(valid_refs) or (
            not cited_refs and ABSTENTION not in answer
        ):
            answer = ABSTENTION
            evidence = []
        elif ABSTENTION in answer:
            evidence = []
        else:
            evidence = [
                item
                for index, item in enumerate(evidence, start=1)
                if f"S{index}" in cited_refs
            ]
        citations = [
            Citation(
                document_id=item["document_id"],
                filename=item["filename"],
                page=item.get("page"),
                chunk_index=item["chunk_index"],
                char_start=item["char_start"],
                char_end=item["char_end"],
                excerpt=item["text"].strip()[:500],
            )
            for item in evidence
        ]
        return ChatResponse(
            answer=answer,
            abstained=not citations,
            citations=citations,
            retrieval_latency_ms=round(retrieval_ms, 2),
            generation_latency_ms=round(generation_ms, 2),
        )

    def health(self) -> tuple[str, str]:
        try:
            self._ensure_collection()
            self.vector_store.health()
            vector_status = "ok"
        except Exception:
            logger.exception("Vector database health check failed")
            vector_status = "unavailable"
        try:
            self.llm.health()
            llm_status = "ok"
        except Exception:
            logger.exception("LLM health check failed")
            llm_status = "unavailable"
        return vector_status, llm_status
