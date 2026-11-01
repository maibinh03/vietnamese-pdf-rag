from typing import Any, Protocol
from uuid import uuid4


class VectorStore(Protocol):
    def ensure_collection(self) -> None: ...

    def upsert(
        self, vectors: list[list[float]], payloads: list[dict[str, Any]]
    ) -> list[str]: ...

    def delete(self, point_ids: list[str]) -> None: ...

    def search(self, vector: list[float], limit: int) -> list[dict[str, Any]]: ...

    def health(self) -> None: ...


class QdrantStore:
    def __init__(self, url: str, collection_name: str, vector_size: int = 384) -> None:
        from qdrant_client import QdrantClient, models

        self.client = QdrantClient(url=url, timeout=5)
        self.collection_name = collection_name
        self.models = models
        self.vector_size = vector_size

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        if any(item.name == self.collection_name for item in collections):
            info = self.client.get_collection(self.collection_name)
            if info.config.params.vectors.size != self.vector_size:
                raise ValueError("Kích thước vector của collection không khớp model.")
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=self.models.VectorParams(
                size=self.vector_size,
                distance=self.models.Distance.COSINE,
            ),
        )

    def upsert(self, vectors: list[list[float]], payloads: list[dict[str, Any]]) -> list[str]:
        ids = [str(uuid4()) for _ in vectors]
        points = [
            self.models.PointStruct(id=point_id, vector=vector, payload=payload)
            for point_id, vector, payload in zip(ids, vectors, payloads, strict=True)
        ]
        self.client.upsert(
            collection_name=self.collection_name, points=points, wait=True
        )
        return ids

    def delete(self, point_ids: list[str]) -> None:
        if point_ids:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=self.models.PointIdsList(points=point_ids),
                wait=True,
            )

    def search(self, vector: list[float], limit: int) -> list[dict[str, Any]]:
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
            with_payload=True,
        )
        return [
            {**(hit.payload or {}), "score": float(hit.score)} for hit in hits
        ]

    def health(self) -> None:
        self.client.get_collections()
