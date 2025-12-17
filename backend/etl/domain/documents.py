from mongoengine import DictField, StringField, UUIDField

from backend.etl.domain.base.nosql import NoSQLBaseDocument
from backend.etl.domain.types import DataCategory


class BaseDocument(NoSQLBaseDocument):
    """Base Mongo document that stores raw extracted content.
    Attributes:
        content (dict): Raw content of the document.
        batch_id (UUID): Identifier of the ingestion batch.
    """

    content = DictField()
    batch_id = UUIDField(binary=False)
    meta = {"abstract": True}


class ArticleDocument(BaseDocument):
    """Raw article stored in Mongo.
    Attributes:
        link (str): URL of the article.
        platform (str): Platform from which the article was sourced.
    """

    link = StringField(required=True, unique=True)
    platform = StringField()
    meta = {"collection": "articles"}

    class Settings:
        """Collection metadata for articles."""

        name = DataCategory.ARTICLES


class YoutubeDocument(BaseDocument):
    """Raw YouTube transcript stored in Mongo.
    Attributes:
        link (str): URL of the YouTube video.
        platform (str): Platform hosting the video.
    """

    link = StringField(required=True, unique=True)
    platform = StringField()
    meta = {"collection": "youtube_videos"}

    class Settings:
        """Collection metadata for videos."""

        name = DataCategory.YOUTUBEVIDEOS


class RepositoryDocument(BaseDocument):
    """Raw repository snapshot stored in Mongo.
    Attributes:
        link (str): URL of the repository.
        name (str): Name of the repository.
        platform (str): Platform hosting the repository.
    """

    link = StringField(required=True, unique=True)
    name = StringField()
    platform = StringField()
    meta = {"collection": "repositories"}

    class Settings:
        """Collection metadata for repositories."""

        name = DataCategory.REPOSITORIES


class PDFDocument(BaseDocument):
    """Raw PDF stored in Mongo.
    Attributes:
        path (str): File path of the PDF document.
        name (str): Name of the PDF document.
        hash (str): Unique hash of the PDF content.
    """

    path = StringField(required=True, unique=True)
    name = StringField()
    hash = StringField(required=True, unique=True)
    meta = {"collection": "pdfs"}

    class Settings:
        """Collection metadata for PDFs."""

        name = DataCategory.PDFS
