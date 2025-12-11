from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the Streamlit client.
    Attributes:
        DEFUALT_API_BASE_URL (str): Base URL for the backend API.
        LOG_FILE_PATH (str): Path to the log file.
        LOG_LEVEL (str): Logging level.
        LOG_ROTATION (str): Log rotation policy.
        LOG_RETENTION (str): Log retention policy.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    DEFUALT_API_BASE_URL: str = "http://localhost:8000/api/v1"
    LOG_FILE_PATH: str = "frontend/logs/frontend.log"
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "5 MB"
    LOG_RETENTION: str = "7 days"


settings = Settings()
