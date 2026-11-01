import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from pdf_rag.config import Settings
from pdf_rag.ingestion import InvalidDocument
from pdf_rag.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentListResponse,
    DocumentResponse,
    HealthResponse,
)
from pdf_rag.service import (
    DependencyUnavailable,
    DuplicateDocument,
    RagService,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(service: RagService | None = None) -> FastAPI:
    settings = service.settings if service else Settings()
    rag = service or RagService(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            rag.initialize()
        except DependencyUnavailable as exc:
            logger.error("Starting in degraded mode: %s", exc)
        yield

    app = FastAPI(title="PDF Document Q&A", version="1.0.0", lifespan=lifespan)
    app.state.rag = rag

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled request error path=%s", request.url.path)
            raise
        logger.info(
            "request path=%s status=%s latency_ms=%.2f",
            request.url.path,
            response.status_code,
            (time.perf_counter() - started) * 1000,
        )
        return response

    @app.exception_handler(DependencyUnavailable)
    async def dependency_error(_: Request, exc: DependencyUnavailable):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        vector_store, llm = rag.health()
        return HealthResponse(
            status="ok" if vector_store == "ok" and llm == "ok" else "degraded",
            vector_store=vector_store,
            llm=llm,
        )

    @app.post("/documents", response_model=DocumentResponse, status_code=201)
    def upload_document(file: Annotated[UploadFile, File()]) -> DocumentResponse:
        filename = file.filename or ""
        if filename.rsplit(".", 1)[-1].lower() not in {"pdf", "txt"}:
            raise HTTPException(status_code=415, detail="Chỉ chấp nhận tệp PDF hoặc TXT.")
        content = file.file.read(settings.max_upload_size_bytes + 1)
        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(status_code=413, detail="Tệp vượt quá giới hạn kích thước.")
        try:
            return rag.ingest(filename, content)
        except InvalidDocument as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except DuplicateDocument as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/documents", response_model=DocumentListResponse)
    def list_documents() -> DocumentListResponse:
        return DocumentListResponse(documents=rag.list_documents())

    @app.post("/chat", response_model=ChatResponse)
    def chat(payload: ChatRequest) -> ChatResponse:
        top_k = payload.top_k or settings.default_top_k
        if top_k > settings.max_top_k:
            raise HTTPException(
                status_code=422,
                detail=f"top_k không được vượt quá {settings.max_top_k}.",
            )
        return rag.chat(payload.question, top_k)

    return app


app = create_app()
