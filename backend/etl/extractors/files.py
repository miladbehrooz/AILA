from loguru import logger
from docling.document_converter import DocumentConverter
from .base import FileExtractor
from backend.etl.domain.documents import PDFDocument


class PDFFileExtractor(FileExtractor):
    model = PDFDocument

    # TODO: Implement the extract method using Langchain docling
    def extract(self, path: str, **kwargs) -> None:
        old_model = self.model.find(path=path)
        if old_model is not None:
            logger.info(f"PDF file already exists in the database: {path}")

            return
        logger.info(f"Starting extracting content from PDF file: {path}")

        file_name = path.split("/")[-1].split(".")[0]

        converter = DocumentConverter()
        content = converter.convert(path)

        content = content.document.export_to_markdown()

        content = {"Content": content}

        instance = self.model(
            path=path,
            content=content,
            name=file_name,
        )
        instance.save()

        logger.info(f"Finished extracting content from PDF file: {path}")


class WordFileExtractor(FileExtractor):

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError


class TextFileExtractor(FileExtractor):

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError


if __name__ == "__main__":
    extractor = PDFFileExtractor()
    extractor.extract("./backend/data/book.pdf")
