from backend.etl import extractors
from backend.etl.domain.documents import ArticleDocument
from urllib.parse import urlparse

from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer

from loguru import logger


from backend.etl.domain.documents import ArticleDocument
from .base import URLExtractor


class ArticleExtractor(URLExtractor):
    model = ArticleDocument

    def extract(self, link: str, **kwargs) -> bool:
        old_model = self.model.find(link=link)
        if old_model is not None:
            logger.info(f"Article already exists in the database: {link}")

            return False

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
        batch_id = kwargs.get("batch_id", "None")

        instance = self.model(
            content=content, link=link, platform=platform, batch_id=batch_id
        )
        instance.save()

        logger.info(f"Finished scrapping article: {link}")
        return True


if __name__ == "__main__":
    extractor = ArticleExtractor()
    extractor.extract("https://weaviate.io/blog/advanced-rag")
