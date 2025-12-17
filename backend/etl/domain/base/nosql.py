import uuid
from datetime import datetime
from typing import Generic, Optional, TypeVar

from loguru import logger
from mongoengine import DateTimeField, Document, UUIDField

from backend.etl.domain.exceptions import ImproperlyConfigured
from backend.infrastructure.db.mongo import MongoDatabaseConnector

_database = MongoDatabaseConnector.connect()


T = TypeVar("T", bound="NoSQLBaseDocument")


class NoSQLBaseDocument(Document, Generic[T]):
    """Base MongoEngine document with conveniences for UUID IDs.
    Attributes:
        id (UUID): Primary key of the document.
        created_at (datetime): Timestamp of document creation.
        updated_at (datetime): Timestamp of last document update.
    """

    id = UUIDField(primary_key=True, binary=False, default=uuid.uuid4)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {"abstract": True, "allow_inheritance": True}

    def save(self, *args, **kwargs) -> "NoSQLBaseDocument":
        """Persist the document while updating the modification timestamp.
        Args:
            *args: Positional arguments for the save operation.
            **kwargs: Keyword arguments for the save operation.
        Returns:
            NoSQLBaseDocument: The saved document instance."""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        """Serialize the document to a JSON-friendly dictionary.
        Returns:
            dict: Dictionary representation of the document with stringified UUIDs.
        """
        data = self.to_mongo().to_dict()
        data["id"] = str(data.pop("_id"))
        for k, v in data.items():
            if isinstance(v, uuid.UUID):
                data[k] = str(v)
        return data

    @classmethod
    def find(cls: type[T], **filter_options) -> Optional[T]:
        """Return the first document that matches the provided filters.
        Args:
            **filter_options: Field-value pairs to filter the documents.
        Returns:
            Optional[T]: The first matching document or None if not found.
        """
        try:
            return cls.objects(**filter_options).first()
        except Exception as e:
            logger.error(f"Failed to retrieve document: {e}")
            return None

    @classmethod
    def bulk_find(cls: type[T], **filter_options) -> list[T]:
        """Return every document that matches the provided filters.
        Args:
            **filter_options: Field-value pairs to filter the documents.
        Returns:
            list[T]: List of matching documents."""
        try:
            return list(cls.objects(**filter_options))
        except Exception as e:
            logger.info(f"Failed to retrieve documents {e}")
            return []

    @classmethod
    def bulk_delete(cls: type[T], **filter_options) -> int:
        """Delete every document that matches the provided filters.
        Args:
            **filter_options: Field-value pairs to filter the documents.
        Returns:
            int: Number of documents deleted.
        """
        try:
            result = cls.objects(**filter_options).delete()
            return result
        except Exception as e:
            logger.error(f"Failed to bulk delete documents: {e}")
            return 0

    @classmethod
    def get_collection_name(cls: type[T]) -> str:
        """Return the Mongo collection name configured on the Settings inner class.
        Raises:
            ImproperlyConfigured: If the Settings class or name attribute is missing.
        Returns:
            str: The name of the MongoDB collection for this document.
        """
        if not hasattr(cls, "Settings") or not hasattr(cls.Settings, "name"):
            raise ImproperlyConfigured(
                f"{cls.__name__} must define a `Settings` class with a `name` attribute to specify collection name."
            )
        return cls.Settings.name
