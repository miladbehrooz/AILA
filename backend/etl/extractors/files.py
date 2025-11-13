from pathlib import Path

from loguru import logger
from docling.document_converter import DocumentConverter
from .base import FileExtractor, ExtractionResult
from backend.etl.domain.documents import PDFDocument
from backend.settings import settings


class PDFFileExtractor(FileExtractor):
    model = PDFDocument

    # TODO: Implement the extract method using Langchain docling
    def extract(self, path: str, **kwargs) -> bool:
        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            resolved_path = (settings.PROJECT_ROOT / resolved_path).resolve()

        old_model = self.model.find(path=path)
        if old_model is not None:
            logger.info(f"PDF file already exists in the database: {path}")

            return ExtractionResult.DUPLICATE
        logger.info(f"Starting extracting content from PDF file: {path}")

        file_name = path.split("/")[-1].split(".")[0]

        converter = DocumentConverter()
        content = converter.convert(str(resolved_path))

        content = content.document.export_to_markdown()

        content = {"Content": content}
        batch_id = kwargs.get("batch_id", "None")

        instance = self.model(
            path=path, content=content, name=file_name, batch_id=batch_id
        )
        instance.save()

        logger.info(f"Finished extracting content from PDF file: {path}")
        return ExtractionResult.INSERTED


class WordFileExtractor(FileExtractor):

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError


class TextFileExtractor(FileExtractor):

    def extract(self, source: str, **kwargs) -> None:
        raise NotImplementedError


if __name__ == "__main__":
    extractor = PDFFileExtractor()
    extractor.extract("./backend/data/book.pdf")
