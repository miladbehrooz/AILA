from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from backend.settings.settings import settings
from backend.utils import logger


class QdrantDatabaseConnector:
    _instance: QdrantClient | None = None

    def __new__(cls, *args, **kwargs) -> QdrantClient:
        if cls._instance is None:
            try:
                cls._instance = QdrantClient(
                    host=settings.QDRANT_DATABASE_HOST,
                    port=settings.QDRANT_DATABASE_PORT,
                )
                uri = f"{settings.QDRANT_DATABASE_HOST}:{settings.QDRANT_DATABASE_PORT}"
                logger.info(f"Connection to Qdrant DB with URI sucessfull: {uri}")

            except UnexpectedResponse:
                logger.exception(
                    "Couldn't connect to Qdrant DB",
                    host=settings.QDRANT_DATABASE_HOST,
                    port=settings.QDRANT_DATABASE_PORT,
                )
                raise
        return cls._instance


connection = QdrantDatabaseConnector()
