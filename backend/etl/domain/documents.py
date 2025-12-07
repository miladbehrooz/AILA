from abc import ABC
from enum import unique
from mongoengine import StringField, DictField, UUIDField
from backend.etl.domain.base.nosql import NoSQLBaseDocument
from backend.etl.domain.types import DataCategory


class BaseDocument(NoSQLBaseDocument):
    content = DictField()
    batch_id = UUIDField(binary=False)
    meta = {"abstract": True}


class ArticleDocument(BaseDocument):
    link = StringField(required=True, unique=True)
    platform = StringField()
    meta = {"collection": "articles"}

    class Settings:
        name = DataCategory.ARTICLES


class YoutubeDocument(BaseDocument):
    link = StringField(required=True, unique=True)
    platform = StringField()
    meta = {"collection": "youtube_videos"}

    class Settings:
        name = DataCategory.YOUTUBEVIDEOS


class RepositoryDocument(BaseDocument):
    link = StringField(required=True, unique=True)
    name = StringField()
    platform = StringField()
    meta = {"collection": "repositories"}

    class Settings:
        name = DataCategory.REPOSITORIES


class PDFDocument(BaseDocument):
    path = StringField(required=True, unique=True)
    name = StringField()
    hash = StringField(required=True, unique=True)
    meta = {"collection": "pdfs"}

    class Settings:
        name = DataCategory.PDFS
