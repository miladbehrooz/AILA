from urllib.parse import urlparse
from uuid import UUID
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from backend.utils import logger
from backend.etl.domain.documents import ArticleDocument
from .base import URLExtractor, ExtractionResult


class ArticleExtractor(URLExtractor):
    """Extractor that scrapes HTML documents and stores them as articles.
    Attributes:
        model (type): The document model associated with articles.
    """

    model = ArticleDocument

    def extract(self, link: str, **kwargs) -> bool:
        """Scrape a URL, transform the HTML into text, and persist the article.

        Args:
            link (str): URL of the article to extract.
            **kwargs: Additional keyword arguments. Must include `batch_id`.

        Returns:
            ExtractionResult: INSERTED when a new article is stored, DUPLICATE when an
                article with the same link already exists.

        Raises:
            ValueError: If `batch_id` is missing or cannot be coerced into a UUID.
        """
        old_model = self.model.find(link=link)
        if old_model is not None:
            logger.info(f"Article already exists in the database: {link}")

            return ExtractionResult.DUPLICATE

        logger.info(f"Starting scrapping article: {link}")

        loader = AsyncHtmlLoader([link])
        docs = loader.load()

        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(docs)
        doc_transformed = docs_transformed[0]
        content = {
            "Title": doc_transformed.metadata.get("title"),
            "Subtitle": doc_transformed.metadata.get("description"),
            "Content": doc_transformed.page_content,
            "language": doc_transformed.metadata.get("language"),
        }

        parsed_url = urlparse(link)
        platform = parsed_url.netloc
        batch_id = kwargs.get("batch_id")
        if batch_id is None:
            raise ValueError("batch_id is required to extract an article.")
        if isinstance(batch_id, str):
            batch_id = UUID(batch_id)

        instance = self.model(
            content=content, link=link, platform=platform, batch_id=batch_id
        )
        instance.save()

        logger.info(f"Finished scrapping article: {link}")
        return ExtractionResult.INSERTED


if __name__ == "__main__":
    extractor = ArticleExtractor()
    extractor.extract("https://weaviate.io/blog/advanced-rag")
