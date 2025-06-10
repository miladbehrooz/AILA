from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from backend.etl.domain.documents import Document
from backend.etl.domain.cleaned_documents import (
    CleanedDocument,
    CleanedArticleDocument,
    CleanedRepositoryDocument,
    CleanedYoutubeDocument,
    PDFCleanedDocument,
)
from backend.etl.domain.documents import (
    ArticleDocument,
    RepositoryDocument,
    YoutubeDocument,
    PDFDocument,
)
from .operations import clean_text


DocumentT = TypeVar("DocumentT", bound=Document)
CleanedDocumentT = TypeVar("CleanedDocumentT", bound=CleanedDocument)


class CleaningDataHandler(ABC, Generic[DocumentT, CleanedDocumentT]):

    @abstractmethod
    def clean(self, data_model: DocumentT) -> CleanedDocumentT:
        pass


class ArticleCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: ArticleDocument) -> CleanedArticleDocument:
        valid_content = [content for content in data_model.content.values() if content]

        return CleanedArticleDocument(
            id=data_model._id,
            content=clean_text(" #### ".join(valid_content)),
            platform=data_model.platform,
            link=data_model.link,
        )


class RepositoryCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: RepositoryDocument) -> CleanedRepositoryDocument:
        return CleanedRepositoryDocument(
            id=data_model._id,
            content=clean_text(" #### ".join(data_model.content.values())),
            platform=data_model.platform,
            name=data_model.name,
            link=data_model.link,
        )


class YoutubeCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: YoutubeDocument) -> CleanedYoutubeDocument:
        return CleanedDocument(
            id=data_model._id,
            content=clean_text(" #### ".join(data_model.content.values())),
            platform=data_model.platform,
            name=data_model.name,
            link=data_model.link,
        )


class PDFCleaningHandler(CleaningDataHandler):
    def clean(self, data_model: PDFDocument) -> PDFCleanedDocument:
        return CleanedDocument(
            id=data_model._id,
            content=clean_text(" #### ".join(data_model.content.values())),
            platform=data_model.platform,
            name=data_model.name,
            path=data_model.path,
        )
