from abc import ABC
from mongoengine import DateTimeField, Document
from datetime import datetime
from typing import Optional, Type, TypeVar, Generic
from loguru import logger
from backend.infrastructure.db.mongo import MongoDatabaseConnector


_database = MongoDatabaseConnector.connect()


T = TypeVar("T", bound="NoSQLBaseDocument")


class NoSQLBaseDocument(Document, Generic[T]):

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {"abstract": True, "allow_inheritance": True}

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self):
        return self.to_mongo().to_dict()

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
