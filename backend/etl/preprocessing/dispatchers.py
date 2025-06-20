from loguru import logger

from .cleaning_data_handlers import (
    CleaningDataHandler,
    ArticleCleaningHandler,
    YoutubeCleaningHandler,
    RepositoryCleaningHandler,
    PDFCleaningHandler,
)
from backend.etl.domain.documents import NoSQLBaseDocument, YoutubeDocument
from backend.etl.domain.cleaned_documents import VectorBaseDocument
from backend.etl.domain.types import DataCategory


class CleaningHandlerFactory:
    @staticmethod
    def create_handler(data_category: DataCategory) -> CleaningDataHandler:
        if data_category == DataCategory.ARTICLES:
            return ArticleCleaningHandler()
        elif data_category == DataCategory.YOUTUBEVIDEOS:
            return YoutubeCleaningHandler()
        elif data_category == DataCategory.REPOSITORIES:
            return RepositoryCleaningHandler()
        elif data_category == DataCategory.PDFS:
            return PDFCleaningHandler()
        else:
            raise ValueError("Unsupported data type")


class CleaningDispatcher:
    factory = CleaningHandlerFactory()

    @classmethod
    def dispatch(cls, data_model: NoSQLBaseDocument) -> VectorBaseDocument:
        data_category = DataCategory(data_model.get_collection_name())
        handler = cls.factory.create_handler(data_category)
        clean_model = handler.clean(data_model)

        logger.info(
            "Document cleaned successfully.",
            data_category=data_category,
            cleaned_content_len=len(clean_model.content),
        )

        return clean_model
