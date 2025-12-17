from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables.
    Attributes:
        LOG_FILE_PATH (str): Path to the log file.
        LOG_LEVEL (str): Logging level.
        LOG_ROTATION (str): Log rotation policy.
        LOG_RETENTION (str): Log retention policy.
        MONGO_DB_NAME (str): Name of the MongoDB database.
        MONGO_DB_HOST (str | None): Host address of the MongoDB database.
        MONGO_DB_USERNAME (str | None): Username for MongoDB authentication.
        MONGO_DB_PASSWORD (str | None): Password for MongoDB authentication.
        QDRANT_DATABASE_HOST (str): Host address of the Qdrant database.
        QDRANT_DATABASE_PORT (int): Port number of the Qdrant database.
        OPENAI_API_KEY (str | None): API key for OpenAI services.
        TEXT_EMBEDDING_PROVIDER (str): Provider for text embeddings.
        TEXT_EMBEDDING_MODEL_NAME (str): Model name for text embeddings.
        AIRFLOW_API_URL (str): Base URL for the Airflow API.
        AIRFLOW_USER (str): Username for Airflow authentication.
        AIRFLOW_PASS (str): Password for Airflow authentication.
        PROJECT_ROOT (Path): Root directory of the project.
        BACKEND_DIR (Path): Directory of the backend code.
        UPLOADS_DIR (Path): Directory for file uploads.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Logging
    LOG_FILE_PATH: str = "backend/logs/aila.log"
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "5 MB"
    LOG_RETENTION: str = "7 days"

    # MongoDB database
    MONGO_DB_NAME: str = "aila"
    MONGO_DB_HOST: str | None = "mongo:27017"
    MONGO_DB_USERNAME: str | None = "aila"
    MONGO_DB_PASSWORD: str | None = "aila"

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

    # File storage
    PROJECT_ROOT: Path = PROJECT_ROOT
    BACKEND_DIR: Path = BACKEND_DIR
    UPLOADS_DIR: Path = BACKEND_DIR / "uploads"


settings = Settings()
