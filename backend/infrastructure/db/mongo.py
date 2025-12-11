from mongoengine import connect
from backend.utils import logger
from backend.settings.settings import settings


class MongoDatabaseConnector:
    """Manage a singleton connection to the Mongo database.
    Attributes:
        _connected (bool): Indicates if a connection has been established.
    """

    _connected: bool = False

    @classmethod
    def connect(cls):
        """Establish a Mongo connection if one doesn't already exist.
        Raises:
            Exception: If the connection to MongoDB fails.
        """
        if not cls._connected:
            try:
                connect(
                    db=settings.MONGO_DB_NAME,
                    host=settings.MONGO_DB_HOST,
                    username=settings.MONGO_DB_USERNAME,
                    password=settings.MONGO_DB_PASSWORD,
                    authentication_source="admin",
                )
                logger.info(
                    f"Connection to MongoDB established: {settings.MONGO_DB_HOST}"
                )
                cls._connected = True
            except Exception as e:
                logger.error(f"Couldn't connect to the database: {e}")
                raise
