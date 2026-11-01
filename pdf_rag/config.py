from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    qdrant_url: str = "http://localhost:6333"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    embedding_model: str = "intfloat/multilingual-e5-small"
    database_path: str = "./data/metadata.db"
    max_upload_size_bytes: int = 10 * 1024 * 1024
    chunk_size: int = 400
    chunk_overlap: int = 80
    default_top_k: int = 5
    max_top_k: int = 10
    min_relevance_score: float = 0.35
    collection_name: str = "bank_documents"
