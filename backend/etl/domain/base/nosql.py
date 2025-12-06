import uuid
from abc import ABC
from mongoengine import DateTimeField, Document, UUIDField
from datetime import datetime
from typing import Optional, Type, TypeVar, Generic
from loguru import logger
from backend.infrastructure.db.mongo import MongoDatabaseConnector
from backend.etl.domain.exceptions import ImproperlyConfigured


_database = MongoDatabaseConnector.connect()


T = TypeVar("T", bound="NoSQLBaseDocument")


class NoSQLBaseDocument(Document, Generic[T]):
    id = UUIDField(primary_key=True, binary=False, default=uuid.uuid4)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {"abstract": True, "allow_inheritance": True}

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        data = self.to_mongo().to_dict()
        data["id"] = str(data.pop("_id"))
        for k, v in data.items():
            if isinstance(v, uuid.UUID):
                data[k] = str(v)
        return data

    @classmethod
    def find(cls: Type[T], **filter_options) -> Optional[T]:
        try:
            return cls.objects(**filter_options).first()
        except Exception as e:
            logger.error(f"Failed to retrieve document: {e}")
            return None

    @classmethod
    def bulk_find(cls: Type[T], **filter_options) -> list[T]:
        try:
            return list(cls.objects(**filter_options))
        except Exception as e:
            logger.info(f"Failed to retrieve documents {e}")
            return []

    @classmethod
    def bulk_delete(cls: Type[T], **filter_options) -> int:
        try:
            result = cls.objects(**filter_options).delete()
            logger.info(f"Deleted {result} documents matching filter {filter_options}.")
            return result
        except Exception as e:
            logger.error(f"Failed to bulk delete documents: {e}")
            return 0

    @classmethod
    def get_collection_name(cls: Type[T]) -> str:
        if not hasattr(cls, "Settings") or not hasattr(cls.Settings, "name"):
            raise ImproperlyConfigured(
                f"{cls.__name__} must define a `Settings` class with a `name` attribute to specify collection name."
            )
        return cls.Settings.name
