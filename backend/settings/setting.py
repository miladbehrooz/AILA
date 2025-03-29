from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # MongoDB database
    MONGO_DB_NAME: str = "laia"
    MONGO_DB_HOST: str | None = "localhost:27017"
    MONGO_DB_USERNAME: str | None = "laia"
    MONGO_DB_PASSWORD: str | None = "laia"


settings = Settings()
