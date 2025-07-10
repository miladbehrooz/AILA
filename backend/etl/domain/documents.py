from abc import ABC

from mongoengine import StringField, DictField
from backend.etl.domain.base.nosql import NoSQLBaseDocument
from backend.etl.domain.types import DataCategory


class BaseDocument(NoSQLBaseDocument):
    content = DictField()
    batch_id = StringField()
    meta = {"abstract": True}


class ArticleDocument(BaseDocument):
    link = StringField()
    platform = StringField()
    meta = {"collection": "articles"}

    class Settings:
        name = DataCategory.ARTICLES


class YoutubeDocument(BaseDocument):
    link = StringField()
    platform = StringField()
    meta = {"collection": "youtube_videos"}

    class Settings:
        name = DataCategory.YOUTUBEVIDEOS


class RepositoryDocument(BaseDocument):
    link = StringField()
    name = StringField()
    platform = StringField()
    meta = {"collection": "repositories"}

    class Settings:
        name = DataCategory.REPOSITORIES


class PDFDocument(BaseDocument):
    path = StringField()
    name = StringField()
    meta = {"collection": "pdfs"}

    class Settings:
        name = DataCategory.PDFS
