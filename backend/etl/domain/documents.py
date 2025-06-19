from abc import ABC

from mongoengine import StringField, DictField
from backend.etl.domain.base.nosql import NoSQLBaseDocument
from backend.etl.domain.types import DataCategory


class BaseDocument(NoSQLBaseDocument):
    content = DictField()
    meta = {"abstract": True}


class ArticleDocument(BaseDocument):
    link = StringField()
    platform = StringField()
    meta = {"collection": "ARTICLES"}

    class Settings:
        name = DataCategory.ARTICLES


class YoutubeDocument(BaseDocument):
    link = StringField()
    platform = StringField()
    meta = {"collection": "YOUTUBEVIDEOS"}

    class Settings:
        name = DataCategory.YOUTUBEVIDEOS


class RepositoryDocument(BaseDocument):
    link = StringField()
    name = StringField()
    platform = StringField()
    meta = {"collection": "REPOSITORIES"}

    class Settings:
        name = DataCategory.REPOSITORIES


class PDFDocument(BaseDocument):
    path = StringField()
    name = StringField()
    meta = {"collection": "PDFS"}

    class Settings:
        name = DataCategory.PDFS
