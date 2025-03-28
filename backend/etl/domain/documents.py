from abc import ABC
from typing import

from .base import NoSQLBaseDocument
from .types import DataCategory



class Document(NoSQLBaseDocument, ABC):

    content: dict
    platform: str


class ArticleDocument(Document):
    link:str

    class Settings:
        name = DataCategory.ARTICLES
    