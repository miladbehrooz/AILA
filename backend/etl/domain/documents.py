from abc import ABC

from mongoengine import StringField, DictField
from backend.etl.domain.base.nosql import NoSQLBaseDocument
from backend.etl.domain.types import DataCategory


class BaseDocument(NoSQLBaseDocument):

    content = DictField()
    platform = StringField()


class ArticleDocument(BaseDocument):
    link = StringField()

    class Settings:
        name = DataCategory.ARTICLES


class YoutubeDocument(BaseDocument):
    link = StringField()

    class Settings:
        name = DataCategory.YOUTUBEVIDEOS


class RepositoryDocument(BaseDocument):
    link = StringField()
    name = StringField()

    class Settings:
        name = DataCategory.REPOSITORIES


class PDFDocument(BaseDocument):
    path = StringField()
    name = StringField()

    class Settings:
        name = DataCategory.PDFS
