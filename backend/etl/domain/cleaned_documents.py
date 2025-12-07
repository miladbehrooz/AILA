from abc import ABC
from typing import Optional

from .base.vector import VectorBaseDocument
from .types import DataCategory


class CleanedDocument(VectorBaseDocument, ABC):
    content: str
    batch_id: str


class CleanedArticleDocument(CleanedDocument):
    platform: str
    link: str
    image: Optional[str] = None

    class Config:
        name = "cleaned_articles"
        category = DataCategory.ARTICLES
        use_vector_index = False


class CleanedYoutubeDocument(CleanedDocument):
    platform: str
    link: str

    class Config:
        name = "cleaned_youtube_videos"
        category = DataCategory.YOUTUBEVIDEOS
        use_vector_index = False


class CleanedRepositoryDocument(CleanedDocument):
    platform: str
    name: str
    link: str

    class Config:
        name = "cleaned_repositories"
        category = DataCategory.REPOSITORIES
        use_vector_index = False


class CleanedPDFDocument(CleanedDocument):
    name: str
    path: str

    class Config:
        name = "cleaned_pdfs"
        category = DataCategory.PDFS
        use_vector_index = False
