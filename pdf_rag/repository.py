import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

from pdf_rag.schemas import DocumentResponse


class DocumentRepository:
    def __init__(self, database_path: str) -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    sha256 TEXT NOT NULL UNIQUE,
                    chunk_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def find_by_hash(self, sha256: str) -> bool:
        with self._connect() as connection:
            return (
                connection.execute(
                    "SELECT 1 FROM documents WHERE sha256 = ?", (sha256,)
                ).fetchone()
                is not None
            )

    def add(
        self,
        document_id: str,
        filename: str,
        sha256: str,
        chunk_count: int,
        created_at: str,
    ) -> DocumentResponse | None:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO documents
                    (id, filename, sha256, chunk_count, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (document_id, filename, sha256, chunk_count, created_at),
            )
            if cursor.rowcount == 0:
                return None
        return DocumentResponse(
            id=document_id,
            filename=filename,
            sha256=sha256,
            chunk_count=chunk_count,
            created_at=created_at,
        )

    def list_documents(self) -> list[DocumentResponse]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, filename, sha256, chunk_count, created_at
                FROM documents ORDER BY created_at, id
                """
            ).fetchall()
        return [DocumentResponse(**dict(row)) for row in rows]
