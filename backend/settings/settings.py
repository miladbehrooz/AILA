from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Logging
    LOG_FILE_PATH: str = "backend/logs/laia.log"
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "5 MB"
    LOG_RETENTION: str = "7 days"

    # MongoDB database
    MONGO_DB_NAME: str = "laia"
    MONGO_DB_HOST: str | None = "mongo:27017"
    MONGO_DB_USERNAME: str | None = "laia"
    MONGO_DB_PASSWORD: str | None = "laia"

    # Qdrant database
    QDRANT_DATABASE_HOST: str = "qdrant"
    QDRANT_DATABASE_PORT: int = "6333"

    # OpenAI API
    OPENAI_API_KEY: str | None = None

    # RAG
    TEXT_EMBEDDING_PROVIDER: str = "huggingface"
    TEXT_EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # Airflow
    AIRFLOW_API_URL: str = "http://localhost:8080/api/v1"
    AIRFLOW_USER: str = "airflow"
    AIRFLOW_PASS: str = "airflow"


settings = Settings()
